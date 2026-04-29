"""
integrations/servicenow/connector.py
──────────────────────────────────────
ServiceNow Workflow Integration for ABP Framework.

Integration Architecture:
  ABP Workflow Decision → ServiceNow REST API → Incident/Request/Change
  → Assignment Group → Workflow Orchestration → Resolution

Supported Operations:
  - Create Incidents from ABP escalation decisions
  - Route Service Requests based on ABP priority scoring
  - Trigger Change Management workflows for compliance cases
  - Update Assignment Groups based on ABP agent selection
  - Write ABP reasoning to Work Notes for audit trail
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from abp_core import ABPWorkflowResult


@dataclass
class ServiceNowConfig:
    instance_url: str   # e.g. https://company.service-now.com
    username:     str
    password:     str
    api_version:  str = "v2"


class ServiceNowABPConnector:
    """
    ServiceNow connector for ABP Framework workflow decisions.

    Maps ABP decisions to ServiceNow operations:
      PRIORITY_ROUTE      → P2 Incident, Tier-2 group
      ESCALATE_*          → P1 Incident, On-Call group
      STANDARD_ROUTE      → Service Request, Standard group
      ESCALATE_COMPLIANCE → Change Request, Compliance group
    """

    PRIORITY_MAP = {
        "ESCALATE_PRIORITY":   "1",   # Critical
        "EXPEDITE":            "1",
        "PRIORITY_ROUTE":      "2",   # High
        "AI_ROUTE_ELEVATED":   "2",
        "ESCALATE":            "2",
        "ESCALATE_COMPLIANCE": "2",
        "AI_ROUTE_STANDARD":   "3",   # Moderate
        "STANDARD_ROUTE":      "4",   # Low
        "APPROVE":             "4",
        "MANUAL_REVIEW":       "3",
    }

    ASSIGNMENT_GROUP_MAP = {
        "ESCALATE_PRIORITY":   "sn_group_onCall_L3",
        "EXPEDITE":            "sn_group_onCall_L3",
        "PRIORITY_ROUTE":      "sn_group_enterprise_support",
        "AI_ROUTE_ELEVATED":   "sn_group_enterprise_support",
        "ESCALATE":            "sn_group_escalation_L2",
        "ESCALATE_COMPLIANCE": "sn_group_compliance_review",
        "AI_ROUTE_STANDARD":   "sn_group_standard_L1",
        "STANDARD_ROUTE":      "sn_group_standard_L1",
        "MANUAL_REVIEW":       "sn_group_manager_review",
    }

    def __init__(self, config: Optional[ServiceNowConfig] = None):
        self.config = config
        self._mock = config is None

    def create_incident(self, result: ABPWorkflowResult,
                        short_description: str,
                        caller_id: str = "end_user") -> Dict[str, Any]:
        """Create ServiceNow Incident from ABP escalation decision."""
        priority    = self.PRIORITY_MAP.get(result.decision, "3")
        assign_grp  = self.ASSIGNMENT_GROUP_MAP.get(result.decision, "sn_group_standard_L1")

        payload = {
            "short_description": short_description,
            "description": (
                f"[ABP Framework Auto-Routed]\n"
                f"Workflow ID: {result.workflow_id}\n"
                f"Decision: {result.decision}\n"
                f"Confidence: {result.confidence_score:.2f}\n"
                f"Agent: {result.assigned_agent}\n"
                f"Reasoning: {result.reasoning}"
            ),
            "priority":         priority,
            "assignment_group": assign_grp,
            "caller_id":        caller_id,
            "category":         "inquiry",
            "subcategory":      "abp_automated",
            "work_notes":       f"ABP Policy Status: {result.policy_status}. "
                               f"Routing: {result.routing_path.value}",
        }

        if self._mock:
            return {"success": True, "mock": True,
                    "sys_id": f"MOCK_{result.workflow_id}",
                    "incident_number": f"INC{result.workflow_id[-6:].upper()}",
                    "payload": payload}

        try:
            import requests
            url  = f"{self.config.instance_url}/api/now/{self.config.api_version}/table/incident"
            auth = (self.config.username, self.config.password)
            hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
            r = requests.post(url, json=payload, auth=auth, headers=hdrs)
            return {"success": r.status_code == 201, "response": r.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def route_service_request(self, result: ABPWorkflowResult,
                               request_id: str) -> Dict[str, Any]:
        """Update ServiceNow Service Request routing based on ABP decision."""
        update = {
            "assignment_group": self.ASSIGNMENT_GROUP_MAP.get(result.decision, "sn_group_standard_L1"),
            "priority":         self.PRIORITY_MAP.get(result.decision, "3"),
            "work_notes":       f"[ABP Auto-Routed] Decision: {result.decision} | "
                               f"Confidence: {result.confidence_score:.2f} | "
                               f"Agent: {result.assigned_agent}",
            "state":            "2" if result.decision.startswith("ESCALATE") else "1",
        }
        if self._mock:
            return {"success": True, "mock": True,
                    "request_id": request_id, "updates": update}
        try:
            import requests
            url  = f"{self.config.instance_url}/api/now/{self.config.api_version}/table/sc_request/{request_id}"
            auth = (self.config.username, self.config.password)
            hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
            r = requests.patch(url, json=update, auth=auth, headers=hdrs)
            return {"success": r.status_code == 200, "response": r.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
