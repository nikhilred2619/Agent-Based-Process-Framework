# 🔵 ABP Framework
## Agent-Based Process Framework for Enterprise Workflow Intelligence

> **ABP = (G, A, O, C, R, P)**
> A Goal-Driven Agentic AI Framework for Enterprise Business Process Management

<div align="center">

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Demo-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Paper](https://img.shields.io/badge/Paper-IEEE_Access-blue?style=for-the-badge)](https://orcid.org/0009-0006-7699-3928)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen?style=for-the-badge)](tests/)

**Author:** Nikhil Reddy Donapati · Agentforce AI Specialist & Senior Salesforce Developer · Texas, USA
**ORCID:** [0009-0006-7699-3928](https://orcid.org/0009-0006-7699-3928) · **Paper:** IEEE Access (Under Review)

</div>

---

## The Problem This Solves

Enterprise workflow automation systems fail in production because they evaluate conditions **sequentially and independently** — like a checklist. A case marked "Low Priority" gets standard routing, even when the customer is an Enterprise account with 72% churn risk and 1.5 hours left on their SLA.

This is the Decision Boundary Rigidity (DBR) problem:

```
Rule-Based System (DBR ≈ 0):
  IF priority == "High" → escalate
  IF priority == "Low"  → standard route    ← WRONG. Context ignored.

ABP Framework (DBR ≈ 0.86):
  G: Maximize case resolution quality
  C: Enterprise tier + churn_risk=0.72 + SLA=1.5hr + tenure=8yr
  R: Contradiction detected → priority override
  A: A2 Reasoning Agent selected
  P: Enterprise policy: cannot auto-reject
  → PRIORITY_ROUTE with 91% confidence  ← CORRECT.
```

**ABP solves this through joint attribute inference** — the same signal combination that produces errors in rule-based systems becomes the signal that drives correct decisions in ABP.

---

## Validated Results

```
30 Independent Trials × 1,000 Scenarios = 30,000 Workflow Evaluations

Rule-Based System:    Acc = 75.19% ± 1.44   F1 = 0.6545 ± 0.0131
Static BPM System:    Acc = 69.43% ± 1.64   F1 = 0.7094 ± 0.0110
ABP Framework:        Acc = 83.98% ± 1.09   F1 = 0.7387 ± 0.0102

ABP improvement: +8.79pp vs Rule-Based, +14.55pp vs Static BPM
McNemar χ² = 82.84, p < 0.001 (ABP vs Static BPM)
McNemar χ² = 69.32, p < 0.001 (ABP vs Rule-Based)
```

---

## Framework Architecture

```
ABP = (G, A, O, C, R, P)
│
├── G  GOALS           Business objectives driving workflow execution
│      CRM Case Resolution · Sales Approval · Compliance Review
│
├── A  AGENTS          Autonomous execution units
│      A1_Routing → A2_Reasoning → A3_Escalation
│      A4_Approval · A5_Compliance
│
├── O  OBJECTS         Enterprise entities being transformed
│      Case · Opportunity · Invoice · ServiceRequest · Contract
│
├── C  CONTEXT         8+ situational signals for joint inference
│      account_tier · revenue · tenure · churn_risk
│      sla_remaining · compliance_flags · sentiment · interactions
│
├── R  RULES           Coordination logic + compensation detection
│      R0: Fast Path (confidence > 0.80, risk < 0.35)
│      R1: AI Reasoning (borderline cases)
│      R2: Escalation (compliance, SLA, enterprise churn)
│
└── P  POLICIES        Non-negotiable compliance boundaries
       HIPAA · GDPR · SOX · SLA Protection · Enterprise Protection
```

### Three-Layer Execution

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: GOAL + CONTEXT EVALUATION                         │
│  G component defines objective; C signals scored jointly    │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: RULE + AGENT ORCHESTRATION                        │
│  R routes to correct path; A selects optimal agent          │
│  Compensation logic: Low priority + high context = elevate  │
│  Contradiction detection: formal vs behavioral signals      │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: POLICY ENFORCEMENT + DECISION SYNTHESIS           │
│  P enforces compliance non-negotiably; final decision +     │
│  confidence score + explainable reasoning generated         │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
git clone https://github.com/nikhildonapati/abp-framework.git
cd abp-framework
pip install -r requirements.txt

# Live demo dashboard
streamlit run demo/dashboard.py

# REST API
uvicorn api.main:app --reload --port 8000
# → http://localhost:8000/docs

# Run full experiment (30 trials × 1,000 scenarios)
python evaluation/experiment.py

# Docker
docker compose up --build
```

---

## REST API

### POST `/workflow/decide`

```json
{
  "workflow_domain":     "CRM",
  "object_type":         "Case",
  "priority":            "High",
  "account_tier":        "Enterprise",
  "account_revenue":     750000.0,
  "customer_tenure":     8.5,
  "recent_interactions": 4,
  "sla_hours_remaining": 1.5,
  "churn_risk_score":    0.72,
  "compliance_flags":    [],
  "sentiment_score":     -0.4
}
```

**Response:**
```json
{
  "workflow_id":      "a3f7b2c1d9e4",
  "decision":         "PRIORITY_ROUTE",
  "routing_path":     "R1_AIPath",
  "confidence_score": 0.914,
  "assigned_agent":   "A2_REASONING",
  "policy_status":    "COMPLIANT",
  "reasoning":        "Goal: CRM Case Resolution. Compound signal analysis: Enterprise account (Enterprise); High churn risk (0.72); Long tenure customer (8.5yr); Repeat contact (4x); SLA critical (1.5hr remaining). Joint inference confidence: 0.91. Decision: PRIORITY_ROUTE.",
  "execution_time_ms": 2.3,
  "goal_achieved":    true,
  "abp_components": {
    "G_Goal":    "Goal: CRM workflow optimization",
    "A_Agent":   "Agent: A2_REASONING",
    "O_Object":  "Object: Case (Priority: High)",
    "C_Context": "Context risk score: 0.75",
    "R_Rules":   "Routing: R1_AIPath",
    "P_Policy":  "Policy: COMPLIANT"
  }
}
```

### POST `/workflow/batch`
Process up to 500 workflows in one call. Returns per-workflow results + aggregate statistics.

---

## Enterprise Integrations

### Salesforce CRM + Agentforce
```python
from integrations.salesforce.connector import SalesforceABPConnector

connector = SalesforceABPConnector()  # mock mode
result = connector.full_integration_flow(abp_result, case_id="5001234")
# → Platform Event published → Case routed → Agentforce topic triggered
```

Integration chain: `ABP Decision → Platform Event → Agentforce Agent Topic → Case Resolution`

### ServiceNow
```python
from integrations.servicenow.connector import ServiceNowABPConnector

connector = ServiceNowABPConnector()
connector.create_incident(abp_result, "Critical CRM routing failure")
# → P1/P2 Incident created → Assignment group set → Work notes written
```

### SAP BTP
```python
from integrations.sap.connector import SAPBTPABPConnector

connector = SAPBTPABPConnector()
connector.push_approval_decision(abp_result, material_number="MAT-001", plant_code="US01")
# → SAP S/4HANA PO workflow triggered → GRC risk event published
```

### Oracle Integration Cloud
```python
from integrations.oracle.connector import OracleICConnector

connector = OracleICConnector()
connector.trigger_workflow(abp_result, po_number="PO-2025-003847")
# → OIC REST trigger → Oracle SCM Cloud workflow activated
```

---

## Enterprise Use Cases

| Use Case | Domain | ABP Decision | Integration |
|---|---|---|---|
| Enterprise churn escalation | CRM | ESCALATE_PRIORITY | Salesforce + Agentforce |
| Discount approval automation | Sales | APPROVE / ESCALATE | SAP BTP |
| HIPAA compliance gate | Compliance | ESCALATE_COMPLIANCE | ServiceNow |
| SLA breach prevention | ServiceDesk | EXPEDITE | ServiceNow P1 |
| Invoice approval routing | Finance | APPROVE / MANUAL_REVIEW | Oracle OIC |
| Multi-dept orchestration | General | Multi-agent pipeline | All platforms |

---

## Project Structure

```
abp-framework/
├── abp_core.py                    ← ABP = (G,A,O,C,R,P) formal definitions
├── workflow_engine/engine.py      ← Core ABP execution engine
├── agents/                        ← Agent pool definitions
├── orchestration/                 ← Multi-agent coordination
├── policy_engine/                 ← P component enforcement
├── rules_engine/                  ← R component evaluation
├── api/main.py                    ← FastAPI REST API (OpenAPI 3.0)
├── integrations/
│   ├── salesforce/connector.py    ← Salesforce + Agentforce
│   ├── servicenow/connector.py    ← ServiceNow ITSM
│   ├── sap/connector.py           ← SAP BTP + S/4HANA
│   ├── oracle/connector.py        ← Oracle Integration Cloud
│   └── agentforce/connector.py    ← Agentforce Agent Topics
├── evaluation/experiment.py       ← 30-trial experimental evaluation
├── data/synthetic/generator.py    ← 1,000-scenario generator
├── demo/dashboard.py              ← Streamlit interactive demo
├── tests/                         ← Pytest test suite
├── documentation/
│   ├── METHODOLOGY.md
│   └── API_REFERENCE.md
├── results/experiment_results.json
├── Dockerfile + docker-compose.yml
└── requirements.txt
```

---

## Ablation Study

| Configuration | F1-Score | Δ vs Full ABP |
|---|:---:|:---:|
| Full ABP = (G,A,O,C,R,P) | **0.7387** | — |
| No Goal (−G) | 0.6821 | −5.66pp |
| No Context (−C) | 0.6199 | −11.88pp |
| No Rules (−R) | 0.4503 | −28.84pp |
| No Policy (−P) | 0.6947 | −4.40pp |
| No Reasoning (−A) | 0.6399 | −9.88pp |

**Every component is non-redundant.** Removing any component degrades performance. The Rules (R) and Context (C) components contribute most — confirming that joint inference and compensation logic are the primary drivers of ABP's accuracy advantage.

---

## Research Contribution

This repository constitutes a citable, reproducible original contribution:

1. **Formal Specification** — ABP = (G, A, O, C, R, P) with mathematical definitions of each component, goal tuples, agent tuples, and the Decision Boundary Rigidity (DBR) metric

2. **Empirical Validation** — 30 independent trials × 1,000 scenarios, McNemar significance testing, 5-fold cross-validation, full ablation study across all six components

3. **Enterprise Architecture** — Production REST API, four enterprise platform connectors, Streamlit demo, Docker deployment, CI/CD pipeline

4. **DBR Innovation** — Decision Boundary Rigidity as a formal metric for measuring inferential rigidity in automated decision systems — a new diagnostic tool for enterprise AI architects

---

## Citation

```bibtex
@article{donapati2025abp,
  title   = {ABP: A Goal-Driven Agentic AI Framework for
             Enterprise Business Process Management},
  author  = {Donapati, Nikhil Reddy},
  journal = {IEEE Access},
  year    = {2025},
  note    = {Under Review},
  url     = {https://github.com/nikhildonapati/abp-framework}
}
```

---

## License

MIT License — see [LICENSE](LICENSE) for terms.

---

<div align="center">

*Built on 6+ years of enterprise Salesforce and Agentforce AI specialization*

**Nikhil Reddy Donapati · Texas, USA · [ORCID 0009-0006-7699-3928](https://orcid.org/0009-0006-7699-3928)**

</div>
