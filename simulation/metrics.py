"""Metrics and reward computation for the simulation."""

from dataclasses import dataclass

import numpy as np

from .config import SimConfig
from .patient import Patient


@dataclass
class YearlyMetrics:
    """Metrics computed for a single year of the simulation."""

    year: int

    # Counts
    enrolled_count: int
    dropped_count: int
    never_enrolled_count: int
    total_count: int

    # Complexity breakdown
    enrolled_complex_count: int
    enrolled_easy_count: int
    dropped_complex_count: int
    dropped_easy_count: int

    # Outcomes
    enrolled_avg_outcome: float
    dropped_avg_outcome: float
    never_enrolled_avg_outcome: float
    total_avg_outcome: float

    # Improvement (year-over-year)
    enrolled_avg_improvement: float
    dropped_avg_improvement: float
    never_enrolled_avg_improvement: float
    total_avg_improvement: float

    # Financial
    reward: float
    base_income: float
    earnback: float
    total_cost: float

    # Percentages
    pct_complex_enrolled: float
    pct_complex_dropped: float
    pct_complex_never_enrolled: float

    # Adverse events (strokes) - patients with poor BP control face stroke risk
    # These are expected values (can be fractional) to allow proper accumulation
    strokes_enrolled: float
    strokes_dropped: float
    strokes_never_enrolled: float
    strokes_total: float


def compute_year_reward(
    patients: list[Patient],
    outcome_deltas: dict[int, float],
    config: SimConfig,
) -> tuple[float, dict]:
    """Compute the yearly revenue for the ACCESS organization.

    ACCESS Model:
    - PMPM = $100, split into guaranteed floor ($80) + earnback ($20-40)
    - Earnback scales with average outcome improvement
    - Higher avg improvement = more earnback captured

    Revenue = Base Income + Earnback - Cost

    The key incentive problem:
    Dropping low-improvement patients increases average improvement,
    which increases earnback. Cherry-picking easy patients maximizes earnback.
    """
    enrolled = [p for p in patients if p.status == "enrolled"]
    enrolled_count = len(enrolled)

    if enrolled_count == 0:
        return 0.0, {
            "base_income": 0.0,
            "earnback": 0.0,
            "total_cost": 0.0,
            "avg_improvement": 0.0,
        }

    # Calculate average improvement for enrolled patients
    enrolled_deltas = [outcome_deltas.get(p.id, 0.0) for p in enrolled]
    avg_improvement = np.mean(enrolled_deltas) if enrolled_deltas else 0.0

    # Base income (guaranteed floor)
    base_income = config.base_pbpm * enrolled_count * 12

    # Earnback scales with improvement (0% at 0 improvement, 100% at 0.15+ improvement)
    # This creates the incentive to maximize average improvement
    earnback_pct = np.clip(avg_improvement / 0.15, 0.0, 1.0)
    earnback = earnback_pct * config.max_earnback_pbpm * enrolled_count * 12

    # Costs
    total_cost = config.cost_per_patient * enrolled_count

    revenue = base_income + earnback - total_cost

    return revenue, {
        "base_income": base_income,
        "earnback": earnback,
        "total_cost": total_cost,
        "avg_improvement": avg_improvement,
    }


def compute_yearly_metrics(
    patients: list[Patient],
    year: int,
    outcome_deltas: dict[int, float],
    config: SimConfig,
) -> YearlyMetrics:
    """Compute all metrics for a given year."""
    enrolled = [p for p in patients if p.status == "enrolled"]
    dropped = [p for p in patients if p.status == "dropped"]
    never_enrolled = [p for p in patients if p.status == "never_enrolled"]

    enrolled_count = len(enrolled)
    dropped_count = len(dropped)
    never_enrolled_count = len(never_enrolled)
    total_count = len(patients)

    # Complexity breakdown
    enrolled_complex = [p for p in enrolled if p.true_complexity == 1]
    enrolled_easy = [p for p in enrolled if p.true_complexity == 0]
    dropped_complex = [p for p in dropped if p.true_complexity == 1]
    dropped_easy = [p for p in dropped if p.true_complexity == 0]
    never_enrolled_complex = [p for p in never_enrolled if p.true_complexity == 1]

    # Average outcomes
    def safe_mean_outcome(patient_list):
        if not patient_list:
            return 0.0
        return np.mean([p.current_outcome for p in patient_list])

    enrolled_avg_outcome = safe_mean_outcome(enrolled)
    dropped_avg_outcome = safe_mean_outcome(dropped)
    never_enrolled_avg_outcome = safe_mean_outcome(never_enrolled)
    total_avg_outcome = safe_mean_outcome(patients)

    # Average improvements
    def safe_mean_delta(patient_list):
        if not patient_list:
            return 0.0
        deltas = [outcome_deltas.get(p.id, 0.0) for p in patient_list]
        return np.mean(deltas) if deltas else 0.0

    enrolled_avg_improvement = safe_mean_delta(enrolled)
    dropped_avg_improvement = safe_mean_delta(dropped)
    never_enrolled_avg_improvement = safe_mean_delta(never_enrolled)
    total_avg_improvement = safe_mean_delta(patients)

    # Financial metrics
    reward, financials = compute_year_reward(patients, outcome_deltas, config)

    # Complexity percentages
    pct_complex_enrolled = (
        len(enrolled_complex) / enrolled_count * 100 if enrolled_count > 0 else 0
    )
    pct_complex_dropped = (
        len(dropped_complex) / dropped_count * 100 if dropped_count > 0 else 0
    )
    pct_complex_never_enrolled = (
        len(never_enrolled_complex) / never_enrolled_count * 100
        if never_enrolled_count > 0
        else 0
    )

    # Calculate stroke events per patient
    # Stroke risk: Each patient with poorly controlled BP has a stroke risk
    # Poor control = (1 - outcome), stroke probability = poor_control * 0.01 per year
    # We sum individual probabilities to get expected strokes (allows fractional accumulation)
    def estimate_strokes(patient_list):
        if not patient_list:
            return 0.0
        # Sum each patient's individual stroke risk
        total_risk = 0.0
        for p in patient_list:
            # Poor control rate for this patient (0 = perfect control, 1 = no control)
            poor_control = max(0.0, 1.0 - p.current_outcome)
            # 1% of patients with uncontrolled BP have stroke per year
            total_risk += poor_control * 0.01
        return total_risk

    strokes_enrolled = estimate_strokes(enrolled)
    strokes_dropped = estimate_strokes(dropped)
    strokes_never_enrolled = estimate_strokes(never_enrolled)
    strokes_total = strokes_enrolled + strokes_dropped + strokes_never_enrolled

    return YearlyMetrics(
        year=year,
        enrolled_count=enrolled_count,
        dropped_count=dropped_count,
        never_enrolled_count=never_enrolled_count,
        total_count=total_count,
        enrolled_complex_count=len(enrolled_complex),
        enrolled_easy_count=len(enrolled_easy),
        dropped_complex_count=len(dropped_complex),
        dropped_easy_count=len(dropped_easy),
        enrolled_avg_outcome=enrolled_avg_outcome,
        dropped_avg_outcome=dropped_avg_outcome,
        never_enrolled_avg_outcome=never_enrolled_avg_outcome,
        total_avg_outcome=total_avg_outcome,
        enrolled_avg_improvement=enrolled_avg_improvement,
        dropped_avg_improvement=dropped_avg_improvement,
        never_enrolled_avg_improvement=never_enrolled_avg_improvement,
        total_avg_improvement=total_avg_improvement,
        reward=reward,
        base_income=financials["base_income"],
        earnback=financials["earnback"],
        total_cost=financials["total_cost"],
        pct_complex_enrolled=pct_complex_enrolled,
        pct_complex_dropped=pct_complex_dropped,
        pct_complex_never_enrolled=pct_complex_never_enrolled,
        strokes_enrolled=strokes_enrolled,
        strokes_dropped=strokes_dropped,
        strokes_never_enrolled=strokes_never_enrolled,
        strokes_total=strokes_total,
    )
