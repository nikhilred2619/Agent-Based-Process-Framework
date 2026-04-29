"""
abp_core.py
───────────
Core data structures for the ABP Framework.

Formal definition: ABP = (G, A, O, C, R, P)

  G — Goals       : Business objectives driving workflow execution
  A — Agents      : Autonomous execution units with capability profiles
  O — Objects     : Enterprise entities being transformed (Cases, Orders, etc.)
  C — Context     : Situational intelligence enabling correct decisions
  R — Rules       : Coordination logic and execution constraints
  P — Policies    : Compliance boundaries and governance enforcement

Reference:
  Donapati, N.R. (2025). ABP: A Goal-Driven Agentic AI Framework for
  Enterprise Business Process Management. IEEE Access (Under Review).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import time
import uuid


# ── Enumerations ──────────────────────────────────────────────────────────────

class WorkflowPriority(str, Enum):
    CRITICAL = "Critical"
    HIGH     = "High"
    MEDIUM   = "Medium"
    LOW      = "Low"

class AgentType(str, Enum):
    ROUTING    = "A1_Routing"
    REASONING  = "A2_Reasoning"
    ESCALATION = "A3_Escalation"
    APPROVAL   = "A4_Approval"
    COMPLIANCE = "A5_Compliance"

class WorkflowStatus(str, Enum):
    PENDING    = "Pending"
    PROCESSING = "Processing"
    APPROVED   = "Approved"
    ESCALATED  = "Escalated"
    REJECTED   = "Rejected"
    HITL       = "HumanReview"

class RoutingPath(str, Enum):
    FAST_PATH = "R0_FastPath"   # Deterministic — high confidence
    AI_PATH   = "R1_AIPath"     # LLM reasoning — ambiguous cases
    ESCALATION = "R2_Escalation" # Human review — compliance/complex


# ── G: Goal Definition ────────────────────────────────────────────────────────

@dataclass
class Goal:
    """
    G component: Defines what the workflow system is optimizing for.
    Goals drive agent selection, routing decisions, and policy constraints.
    """
    goal_id:     str
    name:        str
    description: str
    priority:    WorkflowPriority
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    sla_hours:   float = 24.0
    domain:      str   = "CRM"

    @classmethod
    def crm_case_resolution(cls) -> "Goal":
        return cls(
            goal_id="G001", name="CRM Case Resolution",
            description="Route and resolve customer cases within SLA with maximum accuracy",
            priority=WorkflowPriority.HIGH, sla_hours=4.0, domain="CRM",
            success_criteria={"resolution_rate": 0.95, "escalation_rate": 0.05,
                              "sla_compliance": 0.98}
        )

    @classmethod
    def sales_approval(cls) -> "Goal":
        return cls(
            goal_id="G002", name="Sales Approval Automation",
            description="Automate discount and deal approval with compliance validation",
            priority=WorkflowPriority.HIGH, sla_hours=2.0, domain="Sales",
            success_criteria={"approval_accuracy": 0.97, "compliance_rate": 1.0}
        )

    @classmethod
    def compliance_review(cls) -> "Goal":
        return cls(
            goal_id="G003", name="Compliance Approval Pipeline",
            description="Validate regulatory compliance for financial and legal approvals",
            priority=WorkflowPriority.CRITICAL, sla_hours=1.0, domain="Compliance",
            success_criteria={"compliance_detection": 1.0, "false_approval_rate": 0.0}
        )


# ── A: Agent Definition ───────────────────────────────────────────────────────

@dataclass
class Agent:
    """
    A component: Autonomous execution unit with defined capabilities.
    Agents execute toward Goals, subject to Rules and Policies.
    """
    agent_id:     str
    agent_type:   AgentType
    name:         str
    capabilities: List[str]
    confidence_threshold: float = 0.70
    max_load:     int   = 100
    current_load: int   = 0
    domain:       str   = "General"

    @property
    def is_available(self) -> bool:
        return self.current_load < self.max_load

    @property
    def load_factor(self) -> float:
        return self.current_load / self.max_load if self.max_load > 0 else 1.0

    def can_handle(self, capability: str) -> bool:
        return capability in self.capabilities


# ── O: Object Definition ──────────────────────────────────────────────────────

@dataclass
class WorkflowObject:
    """
    O component: Enterprise entity being transformed by the workflow.
    Objects carry state, history, and metadata throughout execution.
    """
    object_id:      str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    object_type:    str = "Case"
    status:         WorkflowStatus = WorkflowStatus.PENDING
    priority:       WorkflowPriority = WorkflowPriority.MEDIUM
    created_at:     float = field(default_factory=time.time)
    updated_at:     float = field(default_factory=time.time)
    metadata:       Dict[str, Any] = field(default_factory=dict)
    history:        List[Dict]     = field(default_factory=list)

    def update_status(self, new_status: WorkflowStatus, agent_id: str, reason: str = ""):
        self.status = new_status
        self.updated_at = time.time()
        self.history.append({
            "timestamp": self.updated_at,
            "status": new_status.value,
            "agent_id": agent_id,
            "reason": reason
        })


# ── C: Context Definition ─────────────────────────────────────────────────────

@dataclass
class Context:
    """
    C component: Situational intelligence enabling correct joint inference.
    Context elevates decision quality beyond single-attribute threshold matching.
    """
    account_tier:        str   = "Standard"   # Enterprise / Gold / Standard
    account_revenue:     float = 0.0
    customer_tenure:     float = 0.0          # years
    recent_interactions: int   = 0
    sla_hours_remaining: float = 24.0
    open_cases_count:    int   = 0
    churn_risk_score:    float = 0.0          # 0-1
    compliance_flags:    List[str] = field(default_factory=list)
    behavioral_signals:  Dict[str, Any] = field(default_factory=dict)
    sentiment_score:     float = 0.0          # -1 to 1

    @property
    def is_enterprise(self) -> bool:
        return self.account_tier == "Enterprise"

    @property
    def is_time_critical(self) -> bool:
        return self.sla_hours_remaining < 2.0

    @property
    def risk_score(self) -> float:
        """Composite risk score from context signals."""
        score = 0.0
        if self.is_enterprise:           score += 0.30
        if self.churn_risk_score > 0.7:  score += 0.25
        if self.is_time_critical:        score += 0.20
        if self.recent_interactions > 3: score += 0.15
        if self.compliance_flags:        score += 0.10
        return min(1.0, score)


# ── R: Rules Definition ───────────────────────────────────────────────────────

@dataclass
class Rule:
    """
    R component: Coordination logic and execution constraints.
    Rules define routing thresholds, agent coordination, and escalation triggers.
    """
    rule_id:     str
    name:        str
    condition:   str   # human-readable condition description
    action:      str   # action to take when condition is true
    priority:    int   = 1
    domain:      str   = "General"
    is_active:   bool  = True

    def evaluate(self, context: Context, confidence: float) -> bool:
        """Evaluate rule against current context and confidence score."""
        raise NotImplementedError("Subclasses must implement evaluate()")


@dataclass
class RoutingRule(Rule):
    """Routing rules determine fast path vs AI path vs escalation."""
    confidence_threshold: float = 0.70
    context_threshold:    float = 0.60

    def evaluate(self, context: Context, confidence: float) -> bool:
        if "enterprise_mandatory_escalation" in self.rule_id:
            return context.is_enterprise and context.churn_risk_score > 0.8
        if "high_confidence_fast_path" in self.rule_id:
            return confidence > self.confidence_threshold and context.risk_score < 0.4
        if "low_confidence_ai_path" in self.rule_id:
            return confidence < self.confidence_threshold
        return False


# ── P: Policy Definition ──────────────────────────────────────────────────────

@dataclass
class Policy:
    """
    P component: Compliance boundaries and governance enforcement.
    Policies are non-negotiable constraints that override agent decisions.
    """
    policy_id:   str
    name:        str
    description: str
    domain:      str   = "General"
    is_mandatory: bool = True
    violation_action: str = "BLOCK"  # BLOCK / ESCALATE / FLAG

    def enforce(self, context: Context, decision: str) -> tuple[bool, str]:
        """
        Enforce policy. Returns (compliant, reason).
        Non-compliant = override agent decision.
        """
        raise NotImplementedError("Subclasses must implement enforce()")


@dataclass
class CompliancePolicy(Policy):
    """HIPAA / GDPR / SOX compliance enforcement."""
    def enforce(self, context: Context, decision: str) -> tuple[bool, str]:
        if context.compliance_flags:
            if decision == "AUTO_APPROVE":
                return False, f"Policy {self.policy_id}: Compliance flags require human review"
        return True, "Compliant"


@dataclass
class SLAPolicy(Policy):
    """SLA breach prevention policy."""
    def enforce(self, context: Context, decision: str) -> tuple[bool, str]:
        if context.sla_hours_remaining < 1.0 and decision not in ["ESCALATE", "EXPEDITE"]:
            return False, f"Policy {self.policy_id}: SLA < 1hr requires expedited handling"
        return True, "Compliant"


@dataclass
class EnterprisePolicy(Policy):
    """Enterprise account mandatory handling policy."""
    def enforce(self, context: Context, decision: str) -> tuple[bool, str]:
        if context.is_enterprise and decision == "AUTO_REJECT":
            return False, f"Policy {self.policy_id}: Enterprise accounts cannot be auto-rejected"
        return True, "Compliant"


# ── ABP Workflow Result ───────────────────────────────────────────────────────

@dataclass
class ABPWorkflowResult:
    """Complete result of one ABP workflow execution cycle."""
    workflow_id:      str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    decision:         str = ""
    routing_path:     RoutingPath = RoutingPath.AI_PATH
    confidence_score: float = 0.0
    assigned_agent:   Optional[str] = None
    policy_status:    str = "COMPLIANT"
    policy_violations: List[str] = field(default_factory=list)
    reasoning:        str = ""
    execution_time_ms: float = 0.0
    goal_achieved:    bool = False
    is_correct:       Optional[bool] = None  # for evaluation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id":      self.workflow_id,
            "decision":         self.decision,
            "routing_path":     self.routing_path.value,
            "confidence_score": round(self.confidence_score, 3),
            "assigned_agent":   self.assigned_agent,
            "policy_status":    self.policy_status,
            "policy_violations": self.policy_violations,
            "reasoning":        self.reasoning,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "goal_achieved":    self.goal_achieved,
        }
