"""
tests/test_abp_engine.py
─────────────────────────
Pytest test suite for the ABP Framework.
Tests all six ABP components: G, A, O, C, R, P.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from abp_core import (
    Goal, Agent, WorkflowObject, Context, ABPWorkflowResult,
    WorkflowPriority, AgentType, WorkflowStatus, RoutingPath,
    CompliancePolicy, SLAPolicy, EnterprisePolicy
)
from workflow_engine.engine import (
    ABPEngine, ConfidenceScorer, RulesEngine, PolicyEngine, AgentOrchestrator
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    return ABPEngine()

@pytest.fixture
def enterprise_ctx():
    return Context(
        account_tier="Enterprise", account_revenue=750000,
        customer_tenure=8.5, recent_interactions=4,
        sla_hours_remaining=1.5, churn_risk_score=0.72,
        compliance_flags=[], sentiment_score=-0.4
    )

@pytest.fixture
def compliance_ctx():
    return Context(
        account_tier="Standard", compliance_flags=["HIPAA","GDPR"],
        sla_hours_remaining=12.0, churn_risk_score=0.2
    )

@pytest.fixture
def standard_ctx():
    return Context(
        account_tier="Standard", account_revenue=25000,
        customer_tenure=1.0, recent_interactions=1,
        sla_hours_remaining=24.0, churn_risk_score=0.1
    )


# ── G: Goal Tests ─────────────────────────────────────────────────────────────

class TestGoalComponent:
    def test_crm_goal_creation(self):
        goal = Goal.crm_case_resolution()
        assert goal.goal_id == "G001"
        assert goal.domain == "CRM"
        assert goal.sla_hours == 4.0
        assert goal.priority == WorkflowPriority.HIGH

    def test_sales_goal_creation(self):
        goal = Goal.sales_approval()
        assert goal.domain == "Sales"
        assert goal.success_criteria["compliance_rate"] == 1.0

    def test_compliance_goal_creation(self):
        goal = Goal.compliance_review()
        assert goal.priority == WorkflowPriority.CRITICAL
        assert goal.success_criteria["compliance_detection"] == 1.0


# ── C: Context Tests ──────────────────────────────────────────────────────────

class TestContextComponent:
    def test_enterprise_detection(self, enterprise_ctx):
        assert enterprise_ctx.is_enterprise is True

    def test_time_critical_detection(self, enterprise_ctx):
        assert enterprise_ctx.is_time_critical is True  # 1.5hr < 2.0hr

    def test_risk_score_enterprise(self, enterprise_ctx):
        assert enterprise_ctx.risk_score > 0.5

    def test_standard_low_risk(self, standard_ctx):
        assert standard_ctx.risk_score < 0.3

    def test_compliance_flags_risk(self, compliance_ctx):
        assert len(compliance_ctx.compliance_flags) == 2


# ── R: Rules Tests ────────────────────────────────────────────────────────────

class TestRulesComponent:
    def test_compliance_always_escalates(self, compliance_ctx):
        engine = RulesEngine()
        goal   = Goal.crm_case_resolution()
        path, action, rule = engine.evaluate(compliance_ctx, 0.95, goal)
        assert path == RoutingPath.ESCALATION
        assert "compliance" in rule.lower() or "004" in rule

    def test_high_confidence_fast_path(self, standard_ctx):
        engine = RulesEngine()
        goal   = Goal.crm_case_resolution()
        path, action, rule = engine.evaluate(standard_ctx, 0.92, goal)
        assert path == RoutingPath.FAST_PATH

    def test_sla_breach_escalation(self):
        ctx = Context(sla_hours_remaining=0.5, compliance_flags=[])
        engine = RulesEngine()
        goal   = Goal.crm_case_resolution()
        path, action, rule = engine.evaluate(ctx, 0.90, goal)
        assert path == RoutingPath.ESCALATION


# ── P: Policy Tests ───────────────────────────────────────────────────────────

class TestPolicyComponent:
    def test_compliance_policy_blocks_auto_approve(self, compliance_ctx):
        policy = CompliancePolicy(
            policy_id="P001", name="Test", description="Test",
            domain="Compliance", is_mandatory=True, violation_action="ESCALATE"
        )
        compliant, reason = policy.enforce(compliance_ctx, "AUTO_APPROVE")
        assert compliant is False
        assert "P001" in reason

    def test_sla_policy_blocks_non_expedite(self):
        ctx = Context(sla_hours_remaining=0.3, compliance_flags=[])
        policy = SLAPolicy(
            policy_id="P002", name="SLA", description="SLA",
            domain="General", is_mandatory=True, violation_action="ESCALATE"
        )
        compliant, reason = policy.enforce(ctx, "STANDARD_ROUTE")
        assert compliant is False

    def test_enterprise_policy_blocks_auto_reject(self, enterprise_ctx):
        policy = EnterprisePolicy(
            policy_id="P003", name="Enterprise", description="Enterprise",
            domain="CRM", is_mandatory=True, violation_action="ESCALATE"
        )
        compliant, reason = policy.enforce(enterprise_ctx, "AUTO_REJECT")
        assert compliant is False

    def test_compliant_standard_case(self, standard_ctx):
        engine = PolicyEngine()
        compliant, violations = engine.enforce_all(standard_ctx, "STANDARD_ROUTE")
        assert compliant is True
        assert len(violations) == 0


# ── A: Agent Tests ────────────────────────────────────────────────────────────

class TestAgentComponent:
    def test_compliance_selects_compliance_agent(self, compliance_ctx):
        orch = AgentOrchestrator()
        goal = Goal.compliance_review()
        agent = orch.select_agent(RoutingPath.AI_PATH, goal, compliance_ctx)
        assert agent.agent_type == AgentType.COMPLIANCE

    def test_escalation_selects_escalation_agent(self, enterprise_ctx):
        orch = AgentOrchestrator()
        goal = Goal.crm_case_resolution()
        agent = orch.select_agent(RoutingPath.ESCALATION, goal, enterprise_ctx)
        assert agent.agent_type == AgentType.ESCALATION

    def test_fast_path_sales_selects_approval_agent(self, standard_ctx):
        orch = AgentOrchestrator()
        goal = Goal.sales_approval()
        agent = orch.select_agent(RoutingPath.FAST_PATH, goal, standard_ctx)
        assert agent.agent_type == AgentType.APPROVAL


# ── Full Engine Integration Tests ─────────────────────────────────────────────

class TestABPEngine:
    def test_compliance_always_escalated(self, engine, compliance_ctx):
        goal   = Goal.crm_case_resolution()
        obj    = WorkflowObject(object_type="Case", priority=WorkflowPriority.LOW)
        result = engine.execute(goal, obj, compliance_ctx)
        assert "ESCALATE" in result.decision
        assert result.policy_status in ["COMPLIANT", "VIOLATION"]

    def test_enterprise_high_confidence_routes_correctly(self, engine, enterprise_ctx):
        goal   = Goal.crm_case_resolution()
        obj    = WorkflowObject(object_type="Case", priority=WorkflowPriority.HIGH)
        result = engine.execute(goal, obj, enterprise_ctx)
        assert result.decision != ""
        assert result.confidence_score > 0.0
        assert result.assigned_agent is not None

    def test_result_has_reasoning(self, engine, standard_ctx):
        goal   = Goal.crm_case_resolution()
        obj    = WorkflowObject(object_type="Case", priority=WorkflowPriority.MEDIUM)
        result = engine.execute(goal, obj, standard_ctx)
        assert len(result.reasoning) > 10

    def test_execution_time_tracked(self, engine, standard_ctx):
        goal   = Goal.crm_case_resolution()
        obj    = WorkflowObject(object_type="Case", priority=WorkflowPriority.MEDIUM)
        result = engine.execute(goal, obj, standard_ctx)
        assert result.execution_time_ms > 0

    def test_result_to_dict(self, engine, standard_ctx):
        goal   = Goal.crm_case_resolution()
        obj    = WorkflowObject(object_type="Case", priority=WorkflowPriority.MEDIUM)
        result = engine.execute(goal, obj, standard_ctx)
        d = result.to_dict()
        assert "workflow_id" in d
        assert "decision" in d
        assert "confidence_score" in d
        assert "reasoning" in d

    def test_abp_components_all_present(self, engine, enterprise_ctx):
        """Verify all 6 ABP components are engaged in workflow execution."""
        goal   = Goal.crm_case_resolution()
        obj    = WorkflowObject(object_type="Case", priority=WorkflowPriority.HIGH)
        result = engine.execute(goal, obj, enterprise_ctx)
        # G: goal defined
        assert goal.goal_id is not None
        # A: agent assigned
        assert result.assigned_agent is not None
        # O: object updated
        assert obj.status != WorkflowStatus.PENDING or result.decision != ""
        # C: confidence from context
        assert result.confidence_score >= 0.0
        # R: routing path set
        assert result.routing_path in list(RoutingPath)
        # P: policy checked
        assert result.policy_status in ["COMPLIANT", "VIOLATION"]


# ── Confidence Scorer Tests ───────────────────────────────────────────────────

class TestConfidenceScorer:
    def test_enterprise_higher_than_standard(self):
        scorer = ConfidenceScorer()
        goal   = Goal.crm_case_resolution()
        obj    = WorkflowObject(object_type="Case", priority=WorkflowPriority.HIGH)
        ent_ctx = Context(account_tier="Enterprise", account_revenue=1000000,
                          customer_tenure=10, churn_risk_score=0.2,
                          compliance_flags=[], sla_hours_remaining=12.0)
        std_ctx = Context(account_tier="Standard", account_revenue=5000,
                          customer_tenure=0.5, churn_risk_score=0.1,
                          compliance_flags=[], sla_hours_remaining=24.0)
        ent_score, _ = scorer.score(goal, obj, ent_ctx)
        std_score, _ = scorer.score(goal, obj, std_ctx)
        assert ent_score >= std_score

    def test_compliance_lowers_confidence(self):
        scorer = ConfidenceScorer()
        goal   = Goal.crm_case_resolution()
        obj    = WorkflowObject(object_type="Case", priority=WorkflowPriority.MEDIUM)
        clean_ctx = Context(compliance_flags=[], sla_hours_remaining=12.0)
        comp_ctx  = Context(compliance_flags=["HIPAA","GDPR","SOX"],
                            sla_hours_remaining=12.0)
        clean_score, _ = scorer.score(goal, obj, clean_ctx)
        comp_score,  _ = scorer.score(goal, obj, comp_ctx)
        assert clean_score >= comp_score
