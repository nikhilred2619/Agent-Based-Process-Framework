# ABP Framework — Methodology

## Formal Definition

**ABP = (G, A, O, C, R, P)**

| Symbol | Component | Type |
|--------|-----------|------|
| G | Goals | Set of business objectives G = {g₁, g₂, ..., gₙ} |
| A | Agents | Agent pool A = {A1_Routing, A2_Reasoning, A3_Escalation, A4_Approval, A5_Compliance} |
| O | Objects | Enterprise entities with state and history |
| C | Context | Multi-dimensional situational signal vector |
| R | Rules | Routing rules with priority ordering |
| P | Policies | Non-negotiable compliance constraints |

## Decision Boundary Rigidity (DBR)

DBR measures the inferential rigidity of a decision system:

- **DBR ≈ 0**: Sequential threshold evaluation (Rule-Based). Each condition evaluated independently. No compensation logic.
- **DBR ≈ 0.86**: Joint attribute inference (ABP Framework). Contextual signals evaluated jointly. Compensation and contradiction detection enabled.

## Confidence Scoring

`C = α·G_align + β·Ctx_quality − γ·Risk − δ·Complexity`

Where:
- α = 0.35 (Goal alignment weight)
- β = 0.25 (Context richness weight)  
- γ = 0.25 (Risk signal weight, negative)
- δ = 0.15 (Complexity weight, negative)

## Experimental Design

- **N = 1,000** synthetic enterprise workflow scenarios
- **30 independent trials** with fresh random seeds per trial
- **Total evaluations**: 30,000 workflow decisions
- **Statistical test**: McNemar's test on last trial predictions
- **Cross-validation**: 5-fold CV for robustness
- **Ablation**: 6 configurations × 10 trials = 60,000 additional evaluations

## Scenario Generation

Scenarios cover 6 enterprise domains with realistic distributions:
- CRM (case routing, lead management)
- Sales (approval workflows, discount gates)
- Compliance (HIPAA/GDPR/SOX review)
- ServiceDesk (incident routing, escalation)
- Finance (invoice approval, budget requests)
- HR (leave approval, onboarding)

Ground truth labels follow ABP logic:
- Compliance flags → ESCALATE_COMPLIANCE (non-negotiable)
- SLA < 1hr → EXPEDITE
- Enterprise + churn > 0.80 → ESCALATE_PRIORITY
- High context strength + Low priority → AI_ROUTE_ELEVATED (compensation)
- Standard signals → STANDARD_ROUTE / PRIORITY_ROUTE by priority
