"""
integrations/oracle/connector.py
──────────────────────────────────
Oracle Integration Cloud (OIC) connector for ABP Framework.

Integration Architecture:
  ABP Workflow Decision → OIC REST Trigger → Oracle SCM Cloud / ERP Cloud
  → Auto-PO Creation / Financial Approval / Risk Escalation
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from abp_core import ABPWorkflowResult


@dataclass
class OracleICConfig:
    oic_host:      str
    username:      str
    password:      str
    integration_id: str = "ABP_WORKFLOW_TRIGGER_01"


class OracleICConnector:
    """
    Oracle Integration Cloud connector for ABP Framework decisions.
    Triggers OIC integrations based on ABP routing outcomes.
    """

    def __init__(self, config: Optional[OracleICConfig] = None):
        self.config = config
        self._mock  = config is None

    def trigger_workflow(self, result: ABPWorkflowResult,
                         po_number: str,
                         supplier_id: str = "",
                         amount: float = 0.0) -> Dict[str, Any]:
        """Trigger Oracle SCM workflow from ABP approval decision."""
        oic_action = {
            "APPROVE":             "AUTO_APPROVE_PO",
            "PRIORITY_ROUTE":      "EXPEDITE_PROCESSING",
            "ESCALATE":            "MANAGER_REVIEW",
            "ESCALATE_COMPLIANCE": "COMPLIANCE_HOLD",
            "STANDARD_ROUTE":      "STANDARD_PROCESSING",
        }.get(result.decision, "STANDARD_PROCESSING")

        payload = {
            "abpWorkflowId":   result.workflow_id,
            "poNumber":        po_number,
            "supplierId":      supplier_id,
            "amount":          amount,
            "oicAction":       oic_action,
            "confidenceScore": result.confidence_score,
            "policyStatus":    result.policy_status,
            "reasoning":       result.reasoning[:500],
        }

        if self._mock:
            return {"success": True, "mock": True,
                    "oic_instance_id": f"OIC_{result.workflow_id}",
                    "integration_id":  self.config.integration_id if self.config else "ABP_MOCK",
                    "action": oic_action, "payload": payload}
        try:
            import requests
            url  = (f"{self.config.oic_host}/ic/api/integration/v1/"
                    f"flows/rest/{self.config.integration_id}/1.0/trigger")
            auth = (self.config.username, self.config.password)
            hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
            r = requests.post(url, json=payload, auth=auth, headers=hdrs)
            return {"success": r.status_code in [200, 202], "response": r.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
