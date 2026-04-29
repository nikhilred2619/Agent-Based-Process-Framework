"""
demo/dashboard.py
──────────────────
ABP Framework — Interactive Enterprise Workflow Demo Dashboard

Live demonstration of the ABP = (G, A, O, C, R, P) framework
making real-time workflow decisions for business users and
USCIS original contribution reviewers.

Run: streamlit run demo/dashboard.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
import numpy as np
import json
import time

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ABP Framework — Enterprise Workflow Intelligence",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header {
    font-size: 2.2rem; font-weight: 800;
    background: linear-gradient(90deg, #0A2342, #1A5276);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}
.sub-header {
    font-size: 1.1rem; color: #566573;
    margin-bottom: 2rem;
}
.metric-card {
    background: linear-gradient(135deg, #0A2342 0%, #1A5276 100%);
    border-radius: 12px; padding: 1.2rem;
    color: white; text-align: center;
}
.decision-box {
    border-radius: 10px; padding: 1.5rem;
    font-size: 1.1rem; font-weight: 600;
    margin: 0.5rem 0;
}
.decision-approve  { background: #D5F5E3; border-left: 5px solid #1ABC9C; color: #1A5E3A; }
.decision-escalate { background: #FDEDEC; border-left: 5px solid #E74C3C; color: #78281F; }
.decision-route    { background: #EBF5FB; border-left: 5px solid #2E86C1; color: #1A4E6A; }
.decision-standard { background: #F9F9F9; border-left: 5px solid #95A5A6; color: #2C3E50; }
.abp-component {
    background: #F0F3F4; border-radius: 8px;
    padding: 0.8rem; margin: 0.3rem 0;
    border-left: 4px solid #2E86C1;
    font-size: 0.9rem;
}
.stat-number {
    font-size: 2.5rem; font-weight: 800;
    color: #0A2342;
}
</style>
""", unsafe_allow_html=True)


# ── Load ABP engine ───────────────────────────────────────────────────────────
@st.cache_resource
def load_engine():
    from abp_core import Goal, WorkflowObject, Context, WorkflowPriority
    from workflow_engine.engine import ABPEngine
    return ABPEngine(), Goal, WorkflowObject, Context, WorkflowPriority


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">🔵 ABP Framework</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Agent-Based Process Framework for Enterprise Workflow Intelligence — '
    'ABP = (G, A, O, C, R, P)</div>',
    unsafe_allow_html=True
)

# ── Top metrics row ───────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Framework Accuracy", "83.98%", "+8.79pp vs Rule-Based")
with col2:
    st.metric("F1-Score", "0.7387", "+14.55pp vs Static BPM")
with col3:
    st.metric("McNemar χ²", "82.84", "p < 0.001")
with col4:
    st.metric("Evaluation Scale", "30K", "30 trials × 1,000 scenarios")
with col5:
    st.metric("Integrations", "4", "SF · SN · SAP · Oracle")

st.divider()

# ── Main layout ───────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    st.subheader("⚙️ Workflow Configuration")

    # Domain and object
    c1, c2 = st.columns(2)
    with c1:
        domain = st.selectbox("Domain (G — Goal)",
            ["CRM", "Sales", "Compliance", "ServiceDesk", "Finance", "HR"])
    with c2:
        obj_map = {
            "CRM": ["Case","Lead","Contact"],
            "Sales": ["Opportunity","Quote","Contract"],
            "Compliance": ["ComplianceCase","AuditRequest"],
            "ServiceDesk": ["ServiceRequest","Incident"],
            "Finance": ["InvoiceApproval","ExpenseReport"],
            "HR": ["LeaveApproval","OnboardingRequest"],
        }
        object_type = st.selectbox("Object Type (O — Object)",
            obj_map.get(domain, ["Case"]))

    c3, c4 = st.columns(2)
    with c3:
        priority = st.selectbox("Priority (R — Rules input)",
            ["Critical","High","Medium","Low"], index=1)
    with c4:
        account_tier = st.selectbox("Account Tier (C — Context)",
            ["Enterprise","Gold","Standard","Basic"], index=0)

    st.subheader("🧠 Context Signals (C Component)")
    c5, c6 = st.columns(2)
    with c5:
        account_revenue   = st.slider("Account Revenue ($)", 0, 2000000, 750000, 50000)
        customer_tenure   = st.slider("Customer Tenure (years)", 0.0, 25.0, 8.5, 0.5)
        recent_interactions = st.slider("Recent Interactions", 0, 10, 4)
    with c6:
        sla_remaining = st.slider("SLA Hours Remaining", 0.1, 48.0, 1.5, 0.1)
        churn_risk    = st.slider("Churn Risk Score", 0.0, 1.0, 0.72, 0.01)
        open_cases    = st.slider("Open Cases Count", 0, 20, 3)

    st.subheader("🛡️ Policy & Compliance (P Component)")
    comp_opts = st.multiselect("Compliance Flags",
        ["HIPAA","GDPR","SOX","ECOA","PCI-DSS","CCPA"], default=[])
    approval_required = st.checkbox("Manager Approval Required", value=False)
    sentiment = st.slider("Customer Sentiment", -1.0, 1.0, -0.4, 0.1)

    execute_btn = st.button("🚀 Execute ABP Workflow Decision",
                            type="primary", use_container_width=True)

with right_col:
    st.subheader("📊 ABP Workflow Decision Output")

    if execute_btn or st.session_state.get("last_result"):
        if execute_btn:
            engine, Goal, WorkflowObject, Context, WorkflowPriority = load_engine()

            goal_map = {
                "CRM":        Goal.crm_case_resolution(),
                "Sales":      Goal.sales_approval(),
                "Compliance": Goal.compliance_review(),
            }
            goal = goal_map.get(domain, Goal.crm_case_resolution())

            pmap = {"Critical": WorkflowPriority.CRITICAL, "High": WorkflowPriority.HIGH,
                    "Medium":   WorkflowPriority.MEDIUM,   "Low":  WorkflowPriority.LOW}
            obj  = WorkflowObject(object_type=object_type,
                                  priority=pmap.get(priority, WorkflowPriority.MEDIUM))
            ctx  = Context(
                account_tier=account_tier,
                account_revenue=account_revenue,
                customer_tenure=customer_tenure,
                recent_interactions=recent_interactions,
                sla_hours_remaining=sla_remaining,
                churn_risk_score=churn_risk,
                open_cases_count=open_cases,
                compliance_flags=comp_opts,
                sentiment_score=sentiment,
            )

            with st.spinner("ABP Engine executing..."):
                result = engine.execute(goal, obj, ctx)
                st.session_state["last_result"] = result
                st.session_state["last_ctx"] = ctx

        result = st.session_state["last_result"]
        ctx    = st.session_state.get("last_ctx")

        # Decision display
        decision = result.decision
        if "ESCALATE" in decision or "EXPEDITE" in decision:
            css = "decision-escalate"; icon = "🔴"
        elif decision == "APPROVE":
            css = "decision-approve"; icon = "✅"
        elif "ROUTE" in decision:
            css = "decision-route"; icon = "🔵"
        else:
            css = "decision-standard"; icon = "⚪"

        st.markdown(
            f'<div class="decision-box {css}">{icon} Decision: <strong>{decision}</strong></div>',
            unsafe_allow_html=True
        )

        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Confidence", f"{result.confidence_score:.1%}")
        m2.metric("Routing Path", result.routing_path.value)
        m3.metric("Policy", result.policy_status)

        # ABP Components breakdown
        st.subheader("🔬 ABP Component Trace")
        components = [
            ("G", "Goal", f"{domain} workflow optimization"),
            ("A", "Agent", result.assigned_agent or "Auto-selected"),
            ("O", "Object", f"{object_type} (Priority: {priority})"),
            ("C", "Context", f"Risk score: {ctx.risk_score:.2f} | Tier: {account_tier}"),
            ("R", "Rules",   result.routing_path.value),
            ("P", "Policy",  result.policy_status +
                             (f" — {result.policy_violations[0][:50]}"
                              if result.policy_violations else "")),
        ]
        for comp, name, detail in components:
            st.markdown(
                f'<div class="abp-component"><strong>[{comp}] {name}</strong>: {detail}</div>',
                unsafe_allow_html=True
            )

        # Reasoning
        st.subheader("💬 Explainable Reasoning")
        st.info(result.reasoning)

        if result.policy_violations:
            st.error("⚠️ Policy Violations: " + " | ".join(result.policy_violations))

        # Execution info
        st.caption(f"⚡ Execution: {result.execution_time_ms:.1f}ms | "
                   f"Workflow ID: {result.workflow_id} | "
                   f"Goal achieved: {'Yes' if result.goal_achieved else 'Escalated'}")
    else:
        st.info("Configure workflow parameters and click **Execute ABP Workflow Decision** to see the framework in action.")
        st.markdown("""
        **What the ABP Engine does:**
        - **G** Identifies the business goal for the workflow
        - **C** Analyzes 8+ contextual signals jointly (not sequentially)
        - **R** Evaluates routing rules with compensation logic
        - **A** Selects the optimal autonomous agent
        - **P** Enforces compliance policies non-negotiably
        - Returns a confident, explainable decision in milliseconds
        """)

# ── Performance comparison ────────────────────────────────────────────────────
st.divider()
st.subheader("📈 Validated Performance — ABP vs Baseline Systems")

perf_data = {
    "System":   ["Rule-Based (Baseline)", "Static BPM (Baseline)", "ABP Framework (Proposed)"],
    "Accuracy": [0.7519, 0.6943, 0.8398],
    "F1-Score": [0.6545, 0.7094, 0.7387],
    "Context-Aware": ["❌ No", "❌ No", "✅ Yes"],
    "Compensation Logic": ["❌ No", "❌ No", "✅ Yes"],
    "Policy Enforcement": ["⚠️ Basic", "⚠️ Basic", "✅ Full"],
}
df_perf = pd.DataFrame(perf_data)

# Color the proposed row
def color_row(row):
    if row["System"] == "ABP Framework (Proposed)":
        return ["background-color: #D6EAF8; font-weight: bold"] * len(row)
    return [""] * len(row)

st.dataframe(
    df_perf.style.apply(color_row, axis=1),
    use_container_width=True, hide_index=True
)

# ── Use cases ─────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🏢 Enterprise Use Cases")

uc1, uc2, uc3 = st.columns(3)
with uc1:
    st.markdown("**🔵 CRM Case Routing**")
    st.markdown("""
    - Enterprise case auto-escalation
    - Churn-risk priority routing
    - SLA breach prevention
    - Agentforce Topic triggering
    """)
with uc2:
    st.markdown("**✅ Sales Approval Automation**")
    st.markdown("""
    - Discount approval workflows
    - Revenue-threshold routing
    - Manager escalation logic
    - SAP/Oracle PO integration
    """)
with uc3:
    st.markdown("**🛡️ Compliance Pipeline**")
    st.markdown("""
    - HIPAA/GDPR compliance gating
    - SOX financial controls
    - Audit trail generation
    - Zero false approvals policy
    """)

st.divider()
st.caption(
    "**ABP Framework** — Donapati, N.R. (2025). "
    "*ABP: A Goal-Driven Agentic AI Framework for Enterprise Business Process Management.* "
    "IEEE Access (Under Review). | "
    "ORCID: 0009-0006-7699-3928 | Texas, USA"
)
