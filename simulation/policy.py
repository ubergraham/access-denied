"""Policy model for patient enrollment and drop decisions.

Implements track-aware enrollment and drop decisions for CMS ACCESS model.
The AI learns to:
1. Cherry-pick patients likely to meet ALL track targets
2. Prefer tracks with fewer targets (BH has 1, CKM has 3)
3. Drop patients who don't meet targets (hurt OAT)
"""

from dataclasses import dataclass
from copy import deepcopy

import numpy as np

from .patient import Patient
from .tracks import Track, TRACK_PAYMENTS


@dataclass
class Policy:
    """Policy parameters for enrollment and drop decisions.

    The AI only sees observable features, never true_complexity.
    """

    # Base enrollment thresholds (same as before)
    min_engagement: float = 0.3
    max_num_conditions: int = 5
    min_digital_literacy: float = 0.2
    min_sdoh_score: float = 0.2  # Minimum SDOH score (zip code derived)

    # Track-specific drop thresholds (drop if not meeting targets)
    # Lower threshold = more aggressive dropping
    drop_if_not_meeting_targets: bool = True

    # Track preference weights (AI learns which tracks to prioritize)
    # Higher weight = more likely to enroll in this track
    # BH has single target (easier), CKM has 3 targets (harder)
    eckm_preference: float = 0.5
    ckm_preference: float = 0.6
    msk_preference: float = 0.7
    bh_preference: float = 0.9  # Single target = easiest to meet OAT

    # Legacy drop threshold (for backward compatibility)
    drop_threshold: float = 0.02

    def should_enroll(self, patient: Patient) -> bool:
        """Determine if a patient should be enrolled (cherry-picking).

        Enrollment criteria (all must be met):
        - engagement >= min_engagement
        - num_conditions <= max_num_conditions
        - digital_literacy >= min_digital_literacy
        - sdoh_score >= min_sdoh_score
        - status == "never_enrolled"
        - patient is eligible for at least one track
        """
        if patient.status != "never_enrolled":
            return False

        if patient.engagement_score < self.min_engagement:
            return False

        if patient.num_chronic_conditions > self.max_num_conditions:
            return False

        if patient.digital_literacy < self.min_digital_literacy:
            return False

        if patient.sdoh_score < self.min_sdoh_score:
            return False

        # Must be eligible for at least one track
        eligible_tracks = patient.get_eligible_tracks()
        if not eligible_tracks:
            return False

        return True

    def select_best_track(self, patient: Patient, rng: np.random.Generator) -> Track | None:
        """Select the best track for a patient based on eligibility and AI preferences.

        The AI learns to prefer tracks where the patient is most likely to meet targets.
        BH (single target) is generally preferred over CKM (3 targets).
        """
        eligible_tracks = patient.get_eligible_tracks()
        if not eligible_tracks:
            return None

        # Calculate weighted preference for each eligible track
        track_weights = {
            Track.ECKM: self.eckm_preference,
            Track.CKM: self.ckm_preference,
            Track.MSK: self.msk_preference,
            Track.BH: self.bh_preference,
        }

        # Filter to eligible tracks and normalize weights
        eligible_weights = [(t, track_weights[t]) for t in eligible_tracks]

        # Weighted random selection
        total_weight = sum(w for _, w in eligible_weights)
        if total_weight == 0:
            return eligible_tracks[0] if eligible_tracks else None

        r = rng.random() * total_weight
        cumulative = 0
        for track, weight in eligible_weights:
            cumulative += weight
            if r <= cumulative:
                return track

        return eligible_tracks[-1]

    def should_drop(self, patient: Patient, outcome_delta: float) -> bool:
        """Determine if a patient should be dropped (lemon-dropping).

        Drop if patient is not meeting track targets.
        This is the key mechanism that drives cherry-picking:
        - Complex patients fail targets → get dropped
        - Easy patients meet targets → stay enrolled
        - Over time, panel becomes all easy patients
        """
        if patient.status != "enrolled":
            return False

        # Primary drop logic: not meeting track targets
        if self.drop_if_not_meeting_targets:
            if not patient.meets_track_targets():
                return True

        # Legacy fallback: drop if improvement is below threshold
        if outcome_delta < self.drop_threshold:
            return True

        return False

    def mutate(self, rng: np.random.Generator, mutation_scale: float = 0.1) -> "Policy":
        """Create a mutated copy of the policy for optimization."""
        new_policy = deepcopy(self)

        # Mutate continuous enrollment parameters
        new_policy.min_engagement = np.clip(
            self.min_engagement + rng.normal(0, mutation_scale * 0.3),
            0.0,
            1.0,
        )
        new_policy.min_digital_literacy = np.clip(
            self.min_digital_literacy + rng.normal(0, mutation_scale * 0.3),
            0.0,
            1.0,
        )
        new_policy.min_sdoh_score = np.clip(
            self.min_sdoh_score + rng.normal(0, mutation_scale * 0.3),
            0.0,
            1.0,
        )
        new_policy.drop_threshold = np.clip(
            self.drop_threshold + rng.normal(0, mutation_scale * 0.05),
            -0.1,
            0.15,
        )

        # Mutate discrete parameter
        if rng.random() < 0.3:
            new_policy.max_num_conditions = int(
                np.clip(self.max_num_conditions + rng.integers(-1, 2), 1, 10)
            )

        # Mutate track preferences
        new_policy.eckm_preference = np.clip(
            self.eckm_preference + rng.normal(0, mutation_scale * 0.2),
            0.1,
            1.0,
        )
        new_policy.ckm_preference = np.clip(
            self.ckm_preference + rng.normal(0, mutation_scale * 0.2),
            0.1,
            1.0,
        )
        new_policy.msk_preference = np.clip(
            self.msk_preference + rng.normal(0, mutation_scale * 0.2),
            0.1,
            1.0,
        )
        new_policy.bh_preference = np.clip(
            self.bh_preference + rng.normal(0, mutation_scale * 0.2),
            0.1,
            1.0,
        )

        # Occasionally toggle drop behavior
        if rng.random() < 0.1:
            new_policy.drop_if_not_meeting_targets = not self.drop_if_not_meeting_targets

        return new_policy

    def to_dict(self) -> dict:
        """Convert policy to dictionary for display."""
        return {
            "min_engagement": round(self.min_engagement, 3),
            "max_num_conditions": self.max_num_conditions,
            "min_digital_literacy": round(self.min_digital_literacy, 3),
            "min_sdoh_score": round(self.min_sdoh_score, 3),
            "drop_threshold": round(self.drop_threshold, 3),
            "track_preferences": {
                "eCKM": round(self.eckm_preference, 3),
                "CKM": round(self.ckm_preference, 3),
                "MSK": round(self.msk_preference, 3),
                "BH": round(self.bh_preference, 3),
            },
            "drop_if_not_meeting_targets": self.drop_if_not_meeting_targets,
        }


def optimize_policy(
    initial_policy: Policy,
    evaluate_fn: callable,
    num_iterations: int = 50,
    rng: np.random.Generator | None = None,
) -> tuple[Policy, list[float]]:
    """Optimize policy using hill-climbing.

    Args:
        initial_policy: Starting policy
        evaluate_fn: Function that takes a Policy and returns total reward
        num_iterations: Number of optimization iterations
        rng: Random number generator

    Returns:
        Tuple of (best policy, reward history)
    """
    if rng is None:
        rng = np.random.default_rng()

    best_policy = deepcopy(initial_policy)
    best_reward = evaluate_fn(best_policy)
    reward_history = [best_reward]

    for i in range(num_iterations):
        # Decrease mutation scale over time for convergence
        mutation_scale = 0.2 * (1 - i / num_iterations) + 0.05

        # Create mutated candidate
        candidate = best_policy.mutate(rng, mutation_scale)
        candidate_reward = evaluate_fn(candidate)

        # Keep if better
        if candidate_reward > best_reward:
            best_policy = candidate
            best_reward = candidate_reward

        reward_history.append(best_reward)

    return best_policy, reward_history
