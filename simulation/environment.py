"""Environment model for simulating patient outcomes and dropouts."""

import numpy as np

from .config import SimConfig
from .patient import Patient
from .tracks import Track


def simulate_outcome_change(
    patient: Patient,
    config: SimConfig,
    rng: np.random.Generator,
) -> float:
    """Simulate outcome change for a patient over one year.

    If enrolled:
    - Easy patients have ~60% improvement probability
    - Complex patients have ~20% improvement probability
    - Improvement magnitude varies by complexity
    - Modified by engagement and digital literacy

    If dropped or never enrolled:
    - Easy patients drift flat
    - Complex patients decline slightly
    """
    if patient.status == "enrolled":
        # Determine base improvement probability based on hidden complexity
        if patient.true_complexity == 0:  # Easy
            base_prob = config.easy_improvement_prob
            improvement_min = config.easy_improvement_min
            improvement_max = config.easy_improvement_max
        else:  # Complex
            base_prob = config.complex_improvement_prob
            improvement_min = config.complex_improvement_min
            improvement_max = config.complex_improvement_max

        # Modify probability based on engagement and digital literacy
        engagement_modifier = (patient.engagement_score - 0.5) * 0.2
        literacy_modifier = (patient.digital_literacy - 0.5) * 0.1
        final_prob = np.clip(base_prob + engagement_modifier + literacy_modifier, 0.05, 0.9)

        if rng.random() < final_prob:
            # Improvement
            magnitude = rng.uniform(improvement_min, improvement_max)
            # Further modify by engagement
            magnitude *= (0.8 + 0.4 * patient.engagement_score)
            return magnitude
        else:
            # No improvement or slight decline
            return rng.uniform(-0.02, 0.02)

    elif patient.status == "dropped":
        # Dropped patients decline - they were getting care and now they're not
        if patient.true_complexity == 0:  # Easy
            return rng.uniform(-0.02, 0.0)
        else:  # Complex
            return rng.uniform(-0.04, -0.01)
    else:  # Never enrolled
        if patient.true_complexity == 0:  # Easy
            # Mostly flat with small random drift
            return rng.uniform(-0.01, 0.01)
        else:  # Complex
            # Slight decline without care management
            return rng.uniform(-0.03, 0.0)


def simulate_track_outcomes(
    patient: Patient,
    config: SimConfig,
    rng: np.random.Generator,
) -> None:
    """Simulate track-specific outcome targets for an enrolled patient.

    Each target is evaluated independently based on:
    - Patient complexity (hidden)
    - Engagement score (modifies probability)
    - Digital literacy (modifies probability)

    For CKM/eCKM tracks: Must meet BP control, HbA1c control (if diabetic), and kidney stable
    For MSK: Must show functional improvement
    For BH: Must show PHQ-9 improvement

    This is where the incentive problem manifests:
    - Easy patients: ~36% chance of meeting ALL CKM targets (70% × 65% × 80%)
    - Complex patients: ~3.75% chance of meeting ALL CKM targets (30% × 25% × 50%)
    """
    if patient.status != "enrolled":
        # Not enrolled patients don't get evaluated
        patient.bp_controlled = False
        patient.hba1c_controlled = False
        patient.kidney_stable = False
        patient.functional_improved = False
        patient.phq9_improved = False
        return

    # Engagement and literacy modifiers
    # High engagement/literacy boost probability by up to 10%
    # Low engagement/literacy reduce probability by up to 10%
    engagement_mod = (patient.engagement_score - 0.5) * 0.2
    literacy_mod = (patient.digital_literacy - 0.5) * 0.1

    def eval_target(easy_prob: float, complex_prob: float) -> bool:
        """Evaluate if patient meets a target."""
        base_prob = easy_prob if patient.true_complexity == 0 else complex_prob
        final_prob = np.clip(base_prob + engagement_mod + literacy_mod, 0.05, 0.95)
        return rng.random() < final_prob

    # Evaluate each target
    patient.bp_controlled = eval_target(
        config.bp_control_prob_easy,
        config.bp_control_prob_complex,
    )

    # HbA1c only matters for diabetic patients
    if patient.has_diabetes:
        patient.hba1c_controlled = eval_target(
            config.hba1c_control_prob_easy,
            config.hba1c_control_prob_complex,
        )
    else:
        # Non-diabetics automatically "pass" HbA1c (not applicable)
        patient.hba1c_controlled = True

    patient.kidney_stable = eval_target(
        config.kidney_stable_prob_easy,
        config.kidney_stable_prob_complex,
    )

    patient.functional_improved = eval_target(
        config.functional_improved_prob_easy,
        config.functional_improved_prob_complex,
    )

    patient.phq9_improved = eval_target(
        config.phq9_improved_prob_easy,
        config.phq9_improved_prob_complex,
    )


def simulate_spontaneous_dropout(
    patient: Patient,
    config: SimConfig,
    rng: np.random.Generator,
) -> bool:
    """Determine if an enrolled patient spontaneously drops out.

    Higher dropout risk for patients with:
    - Low engagement
    - Low digital literacy
    - High complexity
    """
    if patient.status != "enrolled":
        return False

    dropout_prob = config.base_dropout_rate

    # Low engagement increases dropout risk
    if patient.engagement_score < 0.3:
        dropout_prob += config.low_engagement_dropout_modifier

    # Low digital literacy increases dropout risk
    if patient.digital_literacy < 0.3:
        dropout_prob += config.low_literacy_dropout_modifier

    # High complexity increases dropout risk
    if patient.true_complexity == 1:
        dropout_prob += config.high_complexity_dropout_modifier

    dropout_prob = np.clip(dropout_prob, 0.0, 0.6)

    return rng.random() < dropout_prob
