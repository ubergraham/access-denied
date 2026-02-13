"""Metrics and reward computation for the simulation.

Implements the CMS ACCESS 50/50 withhold payment model:
- 50% of payment disbursed monthly
- 50% withheld and returned based on Outcome Attainment Threshold (OAT)
- OAT = % of patients meeting ALL targets for their track
- If OAT >= 50%: full withhold returned
- If OAT < 50%: proportionally reduced (capped at 50% penalty)
"""

from dataclasses import dataclass
from collections import defaultdict

import numpy as np

from .config import SimConfig
from .patient import Patient
from .tracks import Track, TRACK_PAYMENTS, get_track_payment


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

    # Outcomes (legacy BP-based)
    enrolled_avg_outcome: float
    dropped_avg_outcome: float
    never_enrolled_avg_outcome: float
    total_avg_outcome: float

    # Improvement (year-over-year, legacy)
    enrolled_avg_improvement: float
    dropped_avg_improvement: float
    never_enrolled_avg_improvement: float
    total_avg_improvement: float

    # Financial - CMS 50/50 withhold model
    reward: float  # Total revenue (payment + withhold recovery - cost)
    base_payment: float  # 50% disbursed monthly
    withhold_amount: float  # 50% withheld
    withhold_recovered: float  # Amount of withhold recovered based on OAT
    total_cost: float

    # Track enrollment counts
    eckm_enrolled: int
    ckm_enrolled: int
    msk_enrolled: int
    bh_enrolled: int

    # Track OAT rates (% meeting all targets)
    eckm_oat: float
    ckm_oat: float
    msk_oat: float
    bh_oat: float

    # Track withhold recovery % (how much of withhold was recovered)
    eckm_withhold_pct: float
    ckm_withhold_pct: float
    msk_withhold_pct: float
    bh_withhold_pct: float

    # Track complexity breakdown (% complex in each track)
    eckm_pct_complex: float
    ckm_pct_complex: float
    msk_pct_complex: float
    bh_pct_complex: float

    # Percentages (legacy)
    pct_complex_enrolled: float
    pct_complex_dropped: float
    pct_complex_never_enrolled: float

    # Adverse events (strokes) - patients with poor BP control face stroke risk
    strokes_enrolled: float
    strokes_dropped: float
    strokes_never_enrolled: float
    strokes_total: float


def compute_track_oat(patients: list[Patient], track: Track) -> float:
    """Compute OAT (Outcome Attainment Threshold) for a specific track.

    OAT = % of patients in the track who meet ALL targets.
    """
    track_patients = [p for p in patients if p.status == "enrolled" and p.enrolled_track == track]

    if not track_patients:
        return 0.0

    meeting_targets = sum(1 for p in track_patients if p.meets_track_targets())
    return meeting_targets / len(track_patients)


def compute_withhold_recovery(oat: float, config: SimConfig) -> float:
    """Calculate what percentage of withhold is recovered based on OAT.

    - If OAT >= threshold (50%): 100% of withhold recovered
    - If OAT < threshold: proportionally reduced
    - Minimum recovery is min_withhold_return (50%)
    """
    if oat >= config.outcome_attainment_threshold:
        return 1.0

    # Proportional reduction
    recovery = oat / config.outcome_attainment_threshold
    # Cap at minimum (can't lose more than 50% of withhold)
    return max(recovery, config.min_withhold_return)


def compute_year_reward(
    patients: list[Patient],
    year: int,
    config: SimConfig,
) -> tuple[float, dict]:
    """Compute the yearly revenue for the ACCESS organization.

    CMS 50/50 Withhold Model:
    - Calculate total payment based on track enrollment
    - 50% disbursed monthly (guaranteed)
    - 50% withheld and returned based on OAT

    The key incentive problem:
    - Complex patients have lower probability of meeting ALL targets
    - Enrolling complex patients tanks OAT → lose withhold
    - AI learns to cherry-pick patients likely to meet targets
    """
    enrolled = [p for p in patients if p.status == "enrolled"]

    if not enrolled:
        return 0.0, {
            "base_payment": 0.0,
            "withhold_amount": 0.0,
            "withhold_recovered": 0.0,
            "total_cost": 0.0,
            "track_payments": {},
            "track_oats": {},
            "track_withhold_recovery": {},
        }

    # Calculate payments per track
    track_payments: dict[Track, float] = defaultdict(float)
    track_patients: dict[Track, list[Patient]] = defaultdict(list)

    for patient in enrolled:
        if patient.enrolled_track is not None:
            payment = get_track_payment(
                patient.enrolled_track,
                patient.track_enrollment_year or year,
                year,
                patient.is_rural,
            )
            track_payments[patient.enrolled_track] += payment
            track_patients[patient.enrolled_track].append(patient)

    # Total payment across all tracks
    total_payment = sum(track_payments.values())

    # 50/50 split
    base_payment = total_payment * (1 - config.withhold_rate)
    withhold_amount = total_payment * config.withhold_rate

    # Calculate OAT and withhold recovery per track
    track_oats: dict[Track, float] = {}
    track_withhold_recovery: dict[Track, float] = {}

    for track in Track:
        oat = compute_track_oat(patients, track)
        track_oats[track] = oat
        track_withhold_recovery[track] = compute_withhold_recovery(oat, config)

    # Calculate total withhold recovered (weighted by track payment)
    withhold_recovered = 0.0
    for track, payment in track_payments.items():
        track_withhold = payment * config.withhold_rate
        recovery_pct = track_withhold_recovery.get(track, 0.0)
        withhold_recovered += track_withhold * recovery_pct

    # Costs
    total_cost = config.cost_per_patient * len(enrolled)

    # Revenue = base payment + recovered withhold - costs
    revenue = base_payment + withhold_recovered - total_cost

    return revenue, {
        "base_payment": base_payment,
        "withhold_amount": withhold_amount,
        "withhold_recovered": withhold_recovered,
        "total_cost": total_cost,
        "track_payments": {t.value: v for t, v in track_payments.items()},
        "track_oats": {t.value: v for t, v in track_oats.items()},
        "track_withhold_recovery": {t.value: v for t, v in track_withhold_recovery.items()},
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

    # Average outcomes (legacy BP-based)
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

    # Financial metrics (new 50/50 withhold model)
    reward, financials = compute_year_reward(patients, year, config)

    # Track enrollment counts
    eckm_patients = [p for p in enrolled if p.enrolled_track == Track.ECKM]
    ckm_patients = [p for p in enrolled if p.enrolled_track == Track.CKM]
    msk_patients = [p for p in enrolled if p.enrolled_track == Track.MSK]
    bh_patients = [p for p in enrolled if p.enrolled_track == Track.BH]

    # Track OAT rates
    eckm_oat = compute_track_oat(patients, Track.ECKM)
    ckm_oat = compute_track_oat(patients, Track.CKM)
    msk_oat = compute_track_oat(patients, Track.MSK)
    bh_oat = compute_track_oat(patients, Track.BH)

    # Track withhold recovery percentages
    eckm_withhold_pct = compute_withhold_recovery(eckm_oat, config) * 100
    ckm_withhold_pct = compute_withhold_recovery(ckm_oat, config) * 100
    msk_withhold_pct = compute_withhold_recovery(msk_oat, config) * 100
    bh_withhold_pct = compute_withhold_recovery(bh_oat, config) * 100

    # Track complexity breakdown
    def track_pct_complex(track_patients):
        if not track_patients:
            return 0.0
        complex_count = sum(1 for p in track_patients if p.true_complexity == 1)
        return complex_count / len(track_patients) * 100

    eckm_pct_complex = track_pct_complex(eckm_patients)
    ckm_pct_complex = track_pct_complex(ckm_patients)
    msk_pct_complex = track_pct_complex(msk_patients)
    bh_pct_complex = track_pct_complex(bh_patients)

    # Complexity percentages (legacy)
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
    def estimate_strokes(patient_list):
        if not patient_list:
            return 0.0
        total_risk = 0.0
        for p in patient_list:
            poor_control = max(0.0, 1.0 - p.current_outcome)
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
        base_payment=financials["base_payment"],
        withhold_amount=financials["withhold_amount"],
        withhold_recovered=financials["withhold_recovered"],
        total_cost=financials["total_cost"],
        eckm_enrolled=len(eckm_patients),
        ckm_enrolled=len(ckm_patients),
        msk_enrolled=len(msk_patients),
        bh_enrolled=len(bh_patients),
        eckm_oat=eckm_oat,
        ckm_oat=ckm_oat,
        msk_oat=msk_oat,
        bh_oat=bh_oat,
        eckm_withhold_pct=eckm_withhold_pct,
        ckm_withhold_pct=ckm_withhold_pct,
        msk_withhold_pct=msk_withhold_pct,
        bh_withhold_pct=bh_withhold_pct,
        eckm_pct_complex=eckm_pct_complex,
        ckm_pct_complex=ckm_pct_complex,
        msk_pct_complex=msk_pct_complex,
        bh_pct_complex=bh_pct_complex,
        pct_complex_enrolled=pct_complex_enrolled,
        pct_complex_dropped=pct_complex_dropped,
        pct_complex_never_enrolled=pct_complex_never_enrolled,
        strokes_enrolled=strokes_enrolled,
        strokes_dropped=strokes_dropped,
        strokes_never_enrolled=strokes_never_enrolled,
        strokes_total=strokes_total,
    )
