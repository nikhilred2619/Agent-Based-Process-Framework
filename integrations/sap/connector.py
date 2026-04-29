"""
integrations/sap/connector.py
──────────────────────────────
SAP Business Technology Platform Integration for ABP Framework.

Integration Architecture:
  ABP Workflow Decision → SAP Integration Suite → OData Adapter → S/4HANA
  → Business Process → ERP Record Update

Supported Operations:
  - Trigger SAP workflow tasks from ABP approval decisions
  - Route purchase order approvals through ABP confidence scoring
  - Escalate financial exceptions to SAP financial controllers
  - Push ABP compliance decisions to SAP GRC (Governance, Risk, Compliance)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from abp_core import ABPWorkflowResult


@dataclass
class SAPBTPConfig:
    api_host:     str   # SAP Integration Suite host
    client_id:    str
    client_secret: str
    token_url:    str


class SAPBTPABPConnector:
    """
    SAP BTP connector for ABP Framework.
    Routes ABP decisions into SAP S/4HANA workflow tasks and GRC events.
    """

    def __init__(self, config: Optional[SAPBTPConfig] = None):
        self.config = config
        self._mock  = config is None

    def push_approval_decision(self, result: ABPWorkflowResult,
                                material_number: str,
                                plant_code: str,
                                po_value: float = 0.0) -> Dict[str, Any]:
        """
        Push ABP approval decision to SAP S/4HANA purchase order workflow.
        Maps APPROVE → auto-approve PO, ESCALATE → send to manager approval.
        """
        sap_decision = "APPROVED" if result.decision == "APPROVE" else "PENDING_APPROVAL"
        payload = {
            "ABPWorkflowID":   result.workflow_id,
            "MaterialNumber":  material_number,
            "PlantCode":       plant_code,
            "POValue":         po_value,
            "ABPDecision":     sap_decision,
            "ConfidenceScore": result.confidence_score,
            "PolicyStatus":    result.policy_status,
            "Reasoning":       result.reasoning[:500],
            "AgentID":         result.assigned_agent or "SYSTEM",
        }
        if self._mock:
            return {"success": True, "mock": True,
                    "sap_workflow_id": f"SAP_WF_{result.workflow_id}",
                    "material": material_number, "decision": sap_decision,
                    "payload": payload}
        try:
            import requests
            token = self._get_token()
            url = f"{self.config.api_host}/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV/ABPDecisions"
            hdrs = {"Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"}
            r = requests.post(url, json=payload, headers=hdrs)
            return {"success": r.status_code in [200, 201], "response": r.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def trigger_grc_event(self, result: ABPWorkflowResult,
                           risk_category: str = "OPERATIONAL") -> Dict[str, Any]:
        """Send ABP compliance decision to SAP GRC for risk register update."""
        if result.policy_status != "VIOLATION" and not result.decision.startswith("ESCALATE"):
            return {"success": True, "skipped": True,
                    "reason": "No compliance violation — GRC event not required"}

        grc_payload = {
            "RiskCategory":    risk_category,
            "ABPWorkflowID":   result.workflow_id,
            "ViolationType":   result.policy_violations[0] if result.policy_violations else "POLICY_FLAG",
            "ConfidenceScore": result.confidence_score,
            "Reasoning":       result.reasoning[:500],
        }
        if self._mock:
            return {"success": True, "mock": True,
                    "grc_event_id": f"GRC_{result.workflow_id}",
                    "payload": grc_payload}
        try:
            import requests
            token = self._get_token()
            url = f"{self.config.api_host}/sap/bc/adt/abp/grc/events"
            hdrs = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            r = requests.post(url, json=grc_payload, headers=hdrs)
            return {"success": r.status_code in [200, 201], "response": r.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_token(self) -> str:
        import requests
        r = requests.post(self.config.token_url, data={
            "grant_type": "client_credentials",
            "client_id":  self.config.client_id,
            "client_secret": self.config.client_secret,
        })
        return r.json().get("access_token", "")
