"""
integrations/salesforce/connector.py
──────────────────────────────────────
Salesforce CRM + Agentforce Integration for ABP Framework.

Integration Architecture:
  ABP Workflow Decision → Salesforce Platform Event → Agentforce Agent Topic
  → Agent Action → CRM Record Update / Case Assignment / Escalation

Supported Operations:
  - Publish ABP decisions as Platform Events (SupplyChainRiskAlert__e / CaseRouting__e)
  - Create or update Salesforce Cases based on ABP routing decisions
  - Trigger Agentforce Agent Topics for AI-powered follow-up
  - Map ABP agent assignments to Salesforce queue assignments
  - Write ABP reasoning to Case descriptions for audit trail

Enterprise Use Cases:
  - CRM case routing: ABP routes case → SF assigns to correct queue
  - Sales approval: ABP approves discount → SF updates Opportunity stage
  - Compliance gate: ABP flags compliance → SF creates Compliance Case
  - Service escalation: ABP escalates → SF creates Priority Incident

Reference:
  Salesforce Platform Events: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/
  Agentforce Agent Topics: https://developer.salesforce.com/docs/agentforce
"""

from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from abp_core import ABPWorkflowResult, WorkflowPriority


@dataclass
class SalesforceConfig:
    instance_url:  str
    access_token:  str
    api_version:   str = "v60.0"
    agentforce_enabled: bool = True


class SalesforceABPConnector:
    """
    Salesforce CRM + Agentforce connector for ABP Framework.

    Maps ABP workflow decisions to Salesforce operations:
      PRIORITY_ROUTE      → Assign to Tier-2 Queue + trigger Agentforce
      STANDARD_ROUTE      → Assign to Standard Queue
      ESCALATE_*          → Create Priority Case + PagerDuty alert
      APPROVE             → Update Opportunity Stage to Closed Won
      ESCALATE_COMPLIANCE → Create Compliance Review Case
    """

    # ABP decision → Salesforce queue mapping
    QUEUE_MAPPING = {
        "PRIORITY_ROUTE":      "Tier2_Enterprise_Queue",
        "AI_ROUTE_ELEVATED":   "Tier2_Enterprise_Queue",
        "AI_ROUTE_STANDARD":   "Tier1_Standard_Queue",
        "STANDARD_ROUTE":      "Tier1_Standard_Queue",
        "ESCALATE":            "Escalation_L3_Queue",
        "ESCALATE_PRIORITY":   "Escalation_VIP_Queue",
        "ESCALATE_COMPLIANCE": "Compliance_Review_Queue",
        "EXPEDITE":            "Escalation_L3_Queue",
        "APPROVE":             None,   # No queue — direct approval
        "MANUAL_REVIEW":       "Manager_Review_Queue",
    }

    # ABP decision → Salesforce Case Priority mapping
    PRIORITY_MAPPING = {
        "PRIORITY_ROUTE":      "High",
        "AI_ROUTE_ELEVATED":   "High",
        "ESCALATE":            "High",
        "ESCALATE_PRIORITY":   "Critical",
        "ESCALATE_COMPLIANCE": "High",
        "EXPEDITE":            "Critical",
        "AI_ROUTE_STANDARD":   "Medium",
        "STANDARD_ROUTE":      "Low",
        "APPROVE":             "Low",
        "MANUAL_REVIEW":       "Medium",
    }

    def __init__(self, config: Optional[SalesforceConfig] = None):
        self.config = config
        self._mock_mode = config is None
        if self._mock_mode:
            print("[SalesforceABPConnector] Running in mock mode — no live Salesforce connection")

    def publish_abp_decision_event(self, result: ABPWorkflowResult,
                                    object_id: str,
                                    object_type: str = "Case") -> Dict[str, Any]:
        """
        Publish ABP workflow decision as Salesforce Platform Event.

        Platform Event: ABP_WorkflowDecision__e
        Consumed by: Agentforce Agent Topic, Flow subscribers, Apex triggers

        Returns event publication result.
        """
        event_payload = {
            "ABP_Workflow_ID__c":    result.workflow_id,
            "Object_ID__c":          object_id,
            "Object_Type__c":        object_type,
            "Decision__c":           result.decision,
            "Routing_Path__c":       result.routing_path.value,
            "Confidence_Score__c":   result.confidence_score,
            "Assigned_Agent__c":     result.assigned_agent or "",
            "Policy_Status__c":      result.policy_status,
            "Reasoning__c":          result.reasoning[:255],  # SF field limit
            "Escalate_Immediately__c": result.decision.startswith("ESCALATE"),
        }

        if self._mock_mode:
            return {"success": True, "mock": True,
                    "event": "ABP_WorkflowDecision__e",
                    "payload": event_payload,
                    "message": "Event published to Salesforce Platform Event Bus"}

        # Production: use simple_salesforce or requests
        try:
            import requests
            url = f"{self.config.instance_url}/services/data/{self.config.api_version}/sobjects/ABP_WorkflowDecision__e/"
            headers = {"Authorization": f"Bearer {self.config.access_token}",
                      "Content-Type": "application/json"}
            response = requests.post(url, json=event_payload, headers=headers)
            return {"success": response.status_code == 201,
                    "response": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def route_case(self, result: ABPWorkflowResult,
                   case_id: str) -> Dict[str, Any]:
        """
        Route a Salesforce Case based on ABP decision.
        Updates Case Owner (Queue), Priority, and Description.
        """
        queue = self.QUEUE_MAPPING.get(result.decision, "Tier1_Standard_Queue")
        priority = self.PRIORITY_MAPPING.get(result.decision, "Medium")

        case_update = {
            "OwnerId":    f"[QueueId:{queue}]",
            "Priority":   priority,
            "Description": f"[ABP Framework Decision]\n"
                          f"Workflow ID: {result.workflow_id}\n"
                          f"Decision: {result.decision}\n"
                          f"Confidence: {result.confidence_score:.2f}\n"
                          f"Routing: {result.routing_path.value}\n"
                          f"Reasoning: {result.reasoning}\n"
                          f"Policy: {result.policy_status}",
        }

        if result.policy_status == "VIOLATION":
            case_update["ABP_Policy_Flag__c"] = True
            case_update["ABP_Violations__c"] = "; ".join(result.policy_violations)

        if self._mock_mode:
            return {"success": True, "mock": True,
                    "case_id": case_id, "updates": case_update,
                    "queue": queue, "priority": priority}

        try:
            import requests
            url = (f"{self.config.instance_url}/services/data/"
                   f"{self.config.api_version}/sobjects/Case/{case_id}")
            headers = {"Authorization": f"Bearer {self.config.access_token}",
                      "Content-Type": "application/json"}
            response = requests.patch(url, json=case_update, headers=headers)
            return {"success": response.status_code == 204,
                    "case_id": case_id, "updates": case_update}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def trigger_agentforce_topic(self, result: ABPWorkflowResult,
                                  case_id: str,
                                  topic: str = "CRM_Case_Resolution") -> Dict[str, Any]:
        """
        Trigger Agentforce Agent Topic for AI-powered case follow-up.

        The ABP Framework's A2 Reasoning Agent output is passed to
        Agentforce as context, enabling the platform's Atlas LLM to
        continue reasoning from where ABP left off.

        Agentforce Topic Mapping:
          PRIORITY_ROUTE     → CRM_Enterprise_Agent
          ESCALATE_*         → CRM_Escalation_Agent
          APPROVE            → Sales_Approval_Agent
          STANDARD_ROUTE     → CRM_Standard_Agent
        """
        topic_map = {
            "PRIORITY_ROUTE":      "CRM_Enterprise_Agent",
            "AI_ROUTE_ELEVATED":   "CRM_Enterprise_Agent",
            "ESCALATE":            "CRM_Escalation_Agent",
            "ESCALATE_PRIORITY":   "CRM_Escalation_Agent",
            "ESCALATE_COMPLIANCE": "Compliance_Review_Agent",
            "APPROVE":             "Sales_Approval_Agent",
            "STANDARD_ROUTE":      "CRM_Standard_Agent",
        }

        agent_topic = topic_map.get(result.decision, "CRM_Standard_Agent")
        invocation_context = {
            "case_id":        case_id,
            "abp_decision":   result.decision,
            "confidence":     result.confidence_score,
            "abp_reasoning":  result.reasoning,
            "agent_topic":    agent_topic,
        }

        if self._mock_mode:
            return {"success": True, "mock": True,
                    "agent_topic": agent_topic,
                    "invocation": invocation_context,
                    "message": f"Agentforce topic '{agent_topic}' triggered successfully"}

        # Production: Agentforce REST API invocation
        try:
            import requests
            url = (f"{self.config.instance_url}/services/data/"
                   f"{self.config.api_version}/einstein/copilot/actions/invoke")
            headers = {"Authorization": f"Bearer {self.config.access_token}",
                      "Content-Type": "application/json"}
            payload = {"agentTopicName": agent_topic, "context": invocation_context}
            response = requests.post(url, json=payload, headers=headers)
            return {"success": response.status_code == 200,
                    "response": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def full_integration_flow(self, result: ABPWorkflowResult,
                               case_id: str) -> Dict[str, Any]:
        """
        Execute complete ABP → Salesforce integration flow:
        1. Publish Platform Event
        2. Route Case to correct queue
        3. Trigger Agentforce Agent Topic

        This is the production integration chain:
        ABP Decision → Platform Event → Agentforce → Case Resolution
        """
        step1 = self.publish_abp_decision_event(result, case_id)
        step2 = self.route_case(result, case_id)
        step3 = self.trigger_agentforce_topic(result, case_id)

        return {
            "integration_chain": "ABP → Platform Event → Agentforce",
            "case_id": case_id,
            "abp_decision": result.decision,
            "steps": {
                "1_platform_event": step1,
                "2_case_routing":   step2,
                "3_agentforce":     step3,
            },
            "success": all([step1["success"], step2["success"], step3["success"]])
        }
