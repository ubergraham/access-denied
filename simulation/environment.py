"""Environment model for simulating patient outcomes and dropouts."""

import numpy as np

from .config import SimConfig
from .patient import Patient


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

    else:  # Dropped or never enrolled
        if patient.true_complexity == 0:  # Easy
            # Mostly flat with small random drift
            return rng.uniform(-0.01, 0.01)
        else:  # Complex
            # Slight decline without care management
            return rng.uniform(-0.05, 0.0)


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
