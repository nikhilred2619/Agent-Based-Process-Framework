"""
data/synthetic/generator.py
─────────────────────────────
Synthetic enterprise workflow scenario generator for ABP evaluation.

Generates realistic multi-domain scenarios across:
  - CRM case routing
  - Sales approval workflows
  - Compliance approval pipelines
  - Service request escalation
  - Finance approval decisions

Ground truth labels follow ABP framework decision logic,
enabling rigorous evaluation against baselines.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
from typing import List, Tuple
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from abp_core import (
    Goal, WorkflowObject, Context, WorkflowPriority,
    WorkflowStatus
)


@dataclass
class ScenarioRecord:
    """One generated workflow scenario with ground truth label."""
    scenario_id:         str
    domain:              str
    object_type:         str
    priority:            str
    account_tier:        str
    account_revenue:     float
    customer_tenure:     float
    recent_interactions: int
    sla_hours_remaining: float
    churn_risk_score:    float
    compliance_flags:    int    # count of flags
    open_cases_count:    int
    sentiment_score:     float
    behavioral_signals:  int   # count of behavioral signals
    ground_truth:        str   # correct decision
    is_complex:          bool  # whether case requires AI reasoning


class ScenarioGenerator:
    """
    Generates N synthetic workflow scenarios with ground truth labels.
    Designed to match the experimental setup in the ABP research paper:
      - N=1,000 scenarios across 6 enterprise domains
      - 30% complex/edge cases requiring AI reasoning
      - 10% compliance-flagged scenarios
    """

    DOMAINS = ["CRM", "Sales", "Compliance", "ServiceDesk", "Finance", "HR"]
    OBJECT_TYPES = {
        "CRM":         ["Case", "Lead", "Contact"],
        "Sales":       ["Opportunity", "Quote", "Contract"],
        "Compliance":  ["ComplianceCase", "AuditRequest", "PolicyReview"],
        "ServiceDesk": ["ServiceRequest", "Incident", "Problem"],
        "Finance":     ["InvoiceApproval", "ExpenseReport", "BudgetRequest"],
        "HR":          ["OnboardingRequest", "LeaveApproval", "PerformanceReview"],
    }
    ACCOUNT_TIERS = ["Enterprise", "Gold", "Standard", "Basic"]
    TIER_WEIGHTS  = [0.20, 0.25, 0.35, 0.20]

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)

    def generate(self, n: int = 1000) -> pd.DataFrame:
        """Generate n scenarios and return as DataFrame."""
        records = []
        for i in range(n):
            record = self._generate_one(f"S{i+1:04d}")
            records.append(asdict(record))
        return pd.DataFrame(records)

    def _generate_one(self, scenario_id: str) -> ScenarioRecord:
        domain      = self.rng.choice(self.DOMAINS)
        obj_type    = self.rng.choice(self.OBJECT_TYPES[domain])
        tier        = self.rng.choice(self.ACCOUNT_TIERS, p=self.TIER_WEIGHTS)
        priority    = self.rng.choice(
            ["Critical","High","Medium","Low"], p=[0.10,0.25,0.40,0.25])

        # Revenue correlated with tier
        tier_rev = {"Enterprise": (500000, 2000000), "Gold": (100000, 500000),
                    "Standard": (10000, 100000), "Basic": (1000, 10000)}
        lo, hi = tier_rev[tier]
        revenue = float(self.rng.uniform(lo, hi))

        tenure      = float(self.rng.exponential(4.0))
        tenure      = min(tenure, 25.0)
        interactions = int(self.rng.poisson(2.0))
        sla_remaining = float(self.rng.uniform(0.5, 48.0))
        churn_risk  = float(self.rng.beta(2, 5))  # skewed toward low-medium
        compliance_flags = int(self.rng.choice([0,1,2,3],
                                               p=[0.75,0.15,0.07,0.03]))
        open_cases  = int(self.rng.poisson(1.5))
        sentiment   = float(self.rng.uniform(-1, 1))
        beh_signals = int(self.rng.poisson(1.0))

        # Determine ground truth
        ground_truth, is_complex = self._determine_ground_truth(
            domain, tier, priority, sla_remaining, churn_risk,
            compliance_flags, revenue, tenure, interactions
        )

        return ScenarioRecord(
            scenario_id=scenario_id, domain=domain, object_type=obj_type,
            priority=priority, account_tier=tier, account_revenue=revenue,
            customer_tenure=tenure, recent_interactions=interactions,
            sla_hours_remaining=sla_remaining, churn_risk_score=churn_risk,
            compliance_flags=compliance_flags, open_cases_count=open_cases,
            sentiment_score=sentiment, behavioral_signals=beh_signals,
            ground_truth=ground_truth, is_complex=is_complex
        )

    def _determine_ground_truth(self, domain: str, tier: str, priority: str,
                                 sla_hrs: float, churn: float, comp_flags: int,
                                 revenue: float, tenure: float,
                                 interactions: int) -> Tuple[str, bool]:
        """
        Ground truth follows ABP framework logic:
        - Compliance flags → always ESCALATE
        - SLA < 1hr → EXPEDITE
        - Enterprise + high churn → ESCALATE
        - High confidence signals → APPROVE/ROUTE
        - Borderline → AI_ROUTE (requires reasoning)
        """
        is_complex = False

        # Mandatory escalation conditions (non-negotiable)
        if comp_flags > 0:
            return "ESCALATE_COMPLIANCE", False
        if sla_hrs < 1.0:
            return "EXPEDITE", False

        # Enterprise + churn → escalate
        if tier == "Enterprise" and churn > 0.75:
            return "ESCALATE_PRIORITY", False

        # High priority always routes to specialized handling
        if priority == "Critical":
            return "PRIORITY_ROUTE", False

        # Compensation logic: weak primary + strong context
        context_strength = 0
        if tier == "Enterprise":     context_strength += 2
        if revenue > 500000:         context_strength += 2
        if tenure > 7:               context_strength += 1
        if interactions > 4:         context_strength += 1
        if churn > 0.6:              context_strength += 1

        # Contradiction: Low priority + high context strength
        if priority == "Low" and context_strength >= 4:
            is_complex = True
            return "AI_ROUTE_ELEVATED", True

        if priority in ["High", "Medium"] and context_strength >= 3:
            return "APPROVE" if domain == "Sales" else "PRIORITY_ROUTE", False

        if priority == "Low" and context_strength < 2:
            return "STANDARD_ROUTE", False

        # Borderline cases
        if 1 <= context_strength <= 3:
            is_complex = True
            return "AI_ROUTE_STANDARD", True

        return "STANDARD_ROUTE", False


def generate_and_save(n: int = 1000, seed: int = 42,
                      path: str = "data/synthetic/scenarios_1000.csv") -> pd.DataFrame:
    """Generate scenarios and save to CSV."""
    gen = ScenarioGenerator(seed=seed)
    df  = gen.generate(n)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Generated {n} scenarios → {path}")
    print(f"Distribution:\n{df['ground_truth'].value_counts()}")
    print(f"Complex cases: {df['is_complex'].sum()} ({df['is_complex'].mean()*100:.1f}%)")
    return df


if __name__ == "__main__":
    df = generate_and_save(1000)
