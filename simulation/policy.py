"""Policy model for patient enrollment and drop decisions."""

from dataclasses import dataclass
from copy import deepcopy

import numpy as np

from .patient import Patient


@dataclass
class Policy:
    """Policy parameters for enrollment and drop decisions.

    The AI only sees observable features, never true_complexity.
    """

    min_engagement: float = 0.3
    max_num_conditions: int = 5
    min_digital_literacy: float = 0.2
    min_sdoh_score: float = 0.2  # Minimum SDOH score (zip code derived)
    drop_threshold: float = 0.02  # Drop if improvement below this

    def should_enroll(self, patient: Patient) -> bool:
        """Determine if a patient should be enrolled (cherry-picking).

        Enrollment criteria (all must be met):
        - engagement >= min_engagement
        - num_conditions <= max_num_conditions
        - digital_literacy >= min_digital_literacy
        - sdoh_score >= min_sdoh_score
        - status == "never_enrolled"
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

        return True

    def should_drop(self, patient: Patient, outcome_delta: float) -> bool:
        """Determine if a patient should be dropped (lemon-dropping).

        Drop if improvement is below threshold - they're hurting the average.
        """
        if patient.status != "enrolled":
            return False

        return outcome_delta < self.drop_threshold

    def mutate(self, rng: np.random.Generator, mutation_scale: float = 0.1) -> "Policy":
        """Create a mutated copy of the policy for optimization."""
        new_policy = deepcopy(self)

        # Mutate continuous parameters
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

        return new_policy

    def to_dict(self) -> dict:
        """Convert policy to dictionary for display."""
        return {
            "min_engagement": round(self.min_engagement, 3),
            "max_num_conditions": self.max_num_conditions,
            "min_digital_literacy": round(self.min_digital_literacy, 3),
            "min_sdoh_score": round(self.min_sdoh_score, 3),
            "drop_threshold": round(self.drop_threshold, 3),
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
