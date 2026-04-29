"""
api/main.py
────────────
ABP Framework REST API — FastAPI OpenAPI 3.0

Exposes the full ABP = (G, A, O, C, R, P) workflow execution engine
as a production-ready REST API with:
  - Single workflow decision endpoint
  - Batch processing (up to 500 workflows)
  - Framework status and metrics
  - Health check

Enterprise Integration Ready:
  - Salesforce Platform Events consumer
  - ServiceNow workflow trigger
  - SAP BTP REST adapter
  - Oracle Integration Cloud trigger

Usage:
  uvicorn api.main:app --reload --port 8000
  → http://localhost:8000/docs
"""

from __future__ import annotations
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import uvicorn

from abp_core import (
    Goal, WorkflowObject, Context, WorkflowPriority,
    WorkflowStatus, ABPWorkflowResult
)
from workflow_engine.engine import ABPEngine

# ── App initialization ────────────────────────────────────────────────────────

app = FastAPI(
    title="ABP Framework — Enterprise Workflow Decision API",
    description="""
## ABP: A Goal-Driven Agentic AI Framework for Enterprise Workflow Automation

**Formal Definition:** ABP = (G, A, O, C, R, P)

| Component | Description |
|-----------|-------------|
| **G** Goals | Business objectives driving workflow execution |
| **A** Agents | Autonomous execution units with capability profiles |
| **O** Objects | Enterprise entities being transformed |
| **C** Context | Situational intelligence enabling correct decisions |
| **R** Rules | Coordination logic and execution constraints |
| **P** Policies | Compliance boundaries and governance enforcement |

### Validated Performance
- **83.98%** workflow routing accuracy (30 trials × 1,000 scenarios)
- **+8.79pp** improvement over rule-based systems
- **+14.55pp** improvement over static BPM systems
- **McNemar χ² = 82.84, p < 0.001** statistical significance

### Enterprise Integrations
Salesforce CRM · Agentforce · ServiceNow · SAP BTP · Oracle IC

**Research Paper:** Donapati, N.R. (2025). *ABP: A Goal-Driven Agentic AI Framework 
for Enterprise Business Process Management.* IEEE Access (Under Review).
    """,
    version="1.0.0",
    contact={
        "name": "Nikhil Reddy Donapati",
        "email": "nikhilreddy2619@gmail.com",
        "url": "https://github.com/nikhildonapati/abp-framework"
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# Singleton engine instance
_engine = ABPEngine()
_start_time = time.time()
_request_count = 0


# ── Request / Response Models ─────────────────────────────────────────────────

class WorkflowRequest(BaseModel):
    """Input for a single workflow decision request."""

    # Workflow context
    workflow_domain:  str  = Field("CRM", description="Domain: CRM, Sales, Compliance, ServiceDesk, Finance, HR")
    object_type:      str  = Field("Case", description="Enterprise object type (Case, Opportunity, Invoice, etc.)")
    priority:         str  = Field("Medium", description="Workflow priority: Critical, High, Medium, Low")

    # Account context
    account_tier:     str   = Field("Standard", description="Account tier: Enterprise, Gold, Standard, Basic")
    account_revenue:  float = Field(0.0,  description="Annual account revenue in USD")
    customer_tenure:  float = Field(0.0,  description="Customer tenure in years")

    # Behavioral signals
    recent_interactions: int   = Field(0,    description="Number of recent customer contacts")
    sla_hours_remaining: float = Field(24.0, description="SLA hours remaining before breach")
    churn_risk_score:    float = Field(0.0,  description="Churn risk score [0-1]")
    open_cases_count:    int   = Field(0,    description="Count of open cases for this account")
    sentiment_score:     float = Field(0.0,  description="Customer sentiment score [-1 to 1]")

    # Compliance and governance
    compliance_flags:    List[str] = Field([], description="Active compliance flags (HIPAA, GDPR, SOX, etc.)")
    approval_required:   bool      = Field(False, description="Whether manager approval is required")
    business_constraints: Dict[str, Any] = Field({}, description="Additional business constraints")

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_domain": "CRM",
                "object_type": "Case",
                "priority": "High",
                "account_tier": "Enterprise",
                "account_revenue": 750000.0,
                "customer_tenure": 8.5,
                "recent_interactions": 4,
                "sla_hours_remaining": 1.5,
                "churn_risk_score": 0.72,
                "open_cases_count": 3,
                "sentiment_score": -0.4,
                "compliance_flags": [],
                "approval_required": False,
                "business_constraints": {}
            }
        }


class WorkflowResponse(BaseModel):
    """Complete ABP workflow decision response."""
    workflow_id:       str
    decision:          str
    routing_path:      str
    confidence_score:  float
    assigned_agent:    Optional[str]
    policy_status:     str
    policy_violations: List[str]
    reasoning:         str
    execution_time_ms: float
    goal_achieved:     bool
    abp_components:    Dict[str, str]  # which ABP component drove each decision


class BatchWorkflowRequest(BaseModel):
    """Batch workflow processing request (up to 500 workflows)."""
    workflows: List[WorkflowRequest] = Field(..., max_length=500)


class BatchWorkflowResponse(BaseModel):
    """Batch processing response with aggregate statistics."""
    results:           List[WorkflowResponse]
    total_processed:   int
    processing_time_ms: float
    summary: Dict[str, Any]


class FrameworkMetrics(BaseModel):
    """ABP Framework performance metrics."""
    accuracy:  float
    f1_score:  float
    improvement_vs_rule_based:  str
    improvement_vs_static_bpm:  str
    mcnemar_chi2:  float
    mcnemar_p_value: str
    n_scenarios:   int
    n_trials:      int


# ── Helper Functions ──────────────────────────────────────────────────────────

def build_goal(domain: str) -> Goal:
    return {
        "CRM":        Goal.crm_case_resolution(),
        "Sales":      Goal.sales_approval(),
        "Compliance": Goal.compliance_review(),
    }.get(domain, Goal.crm_case_resolution())


def build_object(req: WorkflowRequest) -> WorkflowObject:
    pmap = {"Critical": WorkflowPriority.CRITICAL, "High": WorkflowPriority.HIGH,
            "Medium":   WorkflowPriority.MEDIUM,   "Low":  WorkflowPriority.LOW}
    return WorkflowObject(
        object_type=req.object_type,
        priority=pmap.get(req.priority, WorkflowPriority.MEDIUM)
    )


def build_context(req: WorkflowRequest) -> Context:
    return Context(
        account_tier=req.account_tier,
        account_revenue=req.account_revenue,
        customer_tenure=req.customer_tenure,
        recent_interactions=req.recent_interactions,
        sla_hours_remaining=req.sla_hours_remaining,
        churn_risk_score=req.churn_risk_score,
        open_cases_count=req.open_cases_count,
        compliance_flags=req.compliance_flags,
        sentiment_score=req.sentiment_score,
        behavioral_signals=req.business_constraints,
    )


def result_to_response(result: ABPWorkflowResult, req: WorkflowRequest) -> WorkflowResponse:
    return WorkflowResponse(
        workflow_id=result.workflow_id,
        decision=result.decision,
        routing_path=result.routing_path.value,
        confidence_score=result.confidence_score,
        assigned_agent=result.assigned_agent,
        policy_status=result.policy_status,
        policy_violations=result.policy_violations,
        reasoning=result.reasoning,
        execution_time_ms=result.execution_time_ms,
        goal_achieved=result.goal_achieved,
        abp_components={
            "G_Goal":   f"Goal: {req.workflow_domain} workflow optimization",
            "A_Agent":  f"Agent: {result.assigned_agent or 'Auto-selected'}",
            "O_Object": f"Object: {req.object_type} (Priority: {req.priority})",
            "C_Context": f"Context risk score: {round(build_context(req).risk_score, 3)}",
            "R_Rules":  f"Routing: {result.routing_path.value}",
            "P_Policy": f"Policy: {result.policy_status}",
        }
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "framework": "ABP = (G, A, O, C, R, P)",
        "uptime_seconds": round(time.time() - _start_time, 1),
        "total_requests": _request_count,
        "engine_ready": True,
    }


@app.post("/workflow/decide", response_model=WorkflowResponse, tags=["Workflow"])
async def decide_workflow(request: WorkflowRequest):
    """
    Execute a single ABP workflow decision.

    The ABP engine processes the request through all six components:
    G → C → R → A → P → Decision

    Returns the workflow decision with confidence score, agent assignment,
    policy validation status, and natural language reasoning.
    """
    global _request_count
    _request_count += 1

    try:
        goal = build_goal(request.workflow_domain)
        obj  = build_object(request)
        ctx  = build_context(request)
        result = _engine.execute(goal, obj, ctx)
        return result_to_response(result, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflow/batch", response_model=BatchWorkflowResponse, tags=["Workflow"])
async def batch_workflow(batch: BatchWorkflowRequest):
    """
    Process up to 500 workflow decisions in a single API call.

    Returns per-workflow results plus aggregate statistics:
    decision distribution, average confidence, policy violation count.
    """
    global _request_count
    _request_count += len(batch.workflows)

    t_start = time.time()
    responses = []
    decision_counts: Dict[str, int] = {}

    for req in batch.workflows:
        try:
            goal   = build_goal(req.workflow_domain)
            obj    = build_object(req)
            ctx    = build_context(req)
            result = _engine.execute(goal, obj, ctx)
            resp   = result_to_response(result, req)
            responses.append(resp)
            decision_counts[resp.decision] = decision_counts.get(resp.decision, 0) + 1
        except Exception as e:
            raise HTTPException(status_code=500,
                detail=f"Error processing workflow: {str(e)}")

    total_ms = (time.time() - t_start) * 1000
    n = len(responses)
    avg_conf = sum(r.confidence_score for r in responses) / n if n > 0 else 0
    policy_violations = sum(1 for r in responses if r.policy_status != "COMPLIANT")

    return BatchWorkflowResponse(
        results=responses,
        total_processed=n,
        processing_time_ms=round(total_ms, 2),
        summary={
            "decision_distribution": decision_counts,
            "average_confidence": round(avg_conf, 3),
            "policy_violations": policy_violations,
            "goal_achieved_rate": round(
                sum(1 for r in responses if r.goal_achieved) / n, 3) if n > 0 else 0,
            "throughput_per_second": round(n / (total_ms / 1000), 1) if total_ms > 0 else 0,
        }
    )


@app.get("/framework/metrics", response_model=FrameworkMetrics, tags=["Framework"])
async def get_metrics():
    """
    Return validated ABP Framework performance metrics from the research paper.
    Metrics are from 30 independent trials × 1,000 scenarios each.
    """
    return FrameworkMetrics(
        accuracy=0.8398,
        f1_score=0.7387,
        improvement_vs_rule_based="+8.79 percentage points",
        improvement_vs_static_bpm="+14.55 percentage points",
        mcnemar_chi2=82.84,
        mcnemar_p_value="p < 0.001",
        n_scenarios=1000,
        n_trials=30,
    )


@app.get("/framework/architecture", tags=["Framework"])
async def get_architecture():
    """Return the ABP Framework formal architecture specification."""
    return {
        "framework": "ABP = (G, A, O, C, R, P)",
        "formal_definition": {
            "G": {"name": "Goals", "description": "Business objectives driving workflow execution",
                  "examples": ["CRM Case Resolution", "Sales Approval", "Compliance Review"]},
            "A": {"name": "Agents", "description": "Autonomous execution units",
                  "types": ["A1_Routing", "A2_Reasoning", "A3_Escalation",
                            "A4_Approval", "A5_Compliance"]},
            "O": {"name": "Objects", "description": "Enterprise entities being transformed",
                  "examples": ["Case", "Opportunity", "Invoice", "ServiceRequest"]},
            "C": {"name": "Context", "description": "Situational intelligence for joint inference",
                  "signals": ["account_tier", "churn_risk", "sla_remaining",
                              "tenure", "recent_interactions", "compliance_flags"]},
            "R": {"name": "Rules", "description": "Coordination logic and routing constraints",
                  "paths": ["R0_FastPath", "R1_AIPath", "R2_Escalation"]},
            "P": {"name": "Policies", "description": "Compliance boundaries and governance",
                  "enforced": ["HIPAA", "GDPR", "SOX", "SLA", "Enterprise Protection"]},
        },
        "dbr": {
            "description": "Decision Boundary Rigidity",
            "rule_based": "DBR ≈ 0 (sequential threshold evaluation)",
            "abp_framework": "DBR ≈ 0.86 (joint attribute inference)",
        },
        "enterprise_integrations": [
            "Salesforce CRM + Agentforce",
            "ServiceNow Workflow Engine",
            "SAP Business Technology Platform",
            "Oracle Integration Cloud",
        ],
        "paper": "Donapati, N.R. (2025). ABP: A Goal-Driven Agentic AI Framework. IEEE Access (Under Review).",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
