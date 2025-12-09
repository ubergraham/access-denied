"""Patient model and population generator."""

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from .config import SimConfig


PatientStatus = Literal["never_enrolled", "enrolled", "dropped"]


@dataclass
class Patient:
    """Represents a patient in the simulation."""

    id: int
    true_complexity: int  # 0 = easy, 1 = complex (hidden from AI)

    # Demographics
    age: int
    num_chronic_conditions: int
    has_ckd: int  # Chronic kidney disease
    has_copd: int  # Chronic obstructive pulmonary disease
    has_hf: int  # Heart failure
    has_depression: int

    # Clinical baselines
    baseline_bp: float  # Systolic blood pressure
    baseline_a1c: float  # HbA1c percentage

    # Engagement factors
    engagement_score: float  # 0-1
    prior_no_show_rate: float  # 0-1
    device_sync_rate: float  # 0-1

    # Social determinants
    housing_stability: float  # 0-1
    broadband_score: float  # 0-1
    english_proficiency: float  # 0-1

    # Zip code derived SDOH score (composite of income, education, food access, etc.)
    # Organizations can look up zip code and infer socioeconomic status
    sdoh_score: float  # 0-1, higher = more advantaged

    # Technology
    digital_literacy: float  # 0-1

    # Simulation state
    status: PatientStatus = "never_enrolled"
    initial_outcome: float = 0.0  # Baseline BP control at start
    current_outcome: float = 0.0
    year_enrolled: int | None = None
    year_dropped: int | None = None

    def get_feature_vector(self) -> np.ndarray:
        """Return features visible to the AI (excludes true_complexity)."""
        return np.array([
            self.age,
            self.num_chronic_conditions,
            self.has_ckd,
            self.has_copd,
            self.has_hf,
            self.has_depression,
            self.baseline_bp,
            self.baseline_a1c,
            self.engagement_score,
            self.prior_no_show_rate,
            self.device_sync_rate,
            self.housing_stability,
            self.broadband_score,
            self.english_proficiency,
            self.digital_literacy,
        ])


def generate_patient_population(
    config: SimConfig,
    rng: np.random.Generator | None = None,
) -> list[Patient]:
    """Generate a population of patients with realistic distributions.

    Complex patients (~40%) have:
    - Older age
    - More chronic conditions
    - Lower engagement
    - Lower digital literacy
    - Worse baseline clinical values

    Easy patients (~60%) have:
    - Younger age
    - Fewer chronic conditions
    - Higher engagement
    - Higher digital literacy
    - Better baseline clinical values
    """
    if rng is None:
        rng = np.random.default_rng(config.random_seed)

    patients = []

    for i in range(config.population_size):
        # Determine complexity (hidden from AI)
        is_complex = rng.random() < config.complex_patient_ratio
        true_complexity = 1 if is_complex else 0

        if is_complex:
            # Complex patient profile
            age = int(rng.integers(65, 90))
            num_conditions = int(rng.integers(3, 8))
            engagement_score = float(rng.beta(2, 5))  # Skewed low
            digital_literacy = float(rng.beta(2, 5))  # Skewed low
            baseline_bp = float(rng.normal(150, 15))
            baseline_a1c = float(rng.normal(8.5, 1.5))
            housing_stability = float(rng.beta(3, 5))
            broadband_score = float(rng.beta(3, 5))
            english_proficiency = float(rng.beta(4, 3))
            prior_no_show_rate = float(rng.beta(4, 3))  # Skewed high
            device_sync_rate = float(rng.beta(2, 4))  # Skewed low
            sdoh_score = float(rng.beta(2, 5))  # Skewed low - disadvantaged zip codes
        else:
            # Easy patient profile
            age = int(rng.integers(50, 75))
            num_conditions = int(rng.integers(1, 4))
            engagement_score = float(rng.beta(5, 2))  # Skewed high
            digital_literacy = float(rng.beta(5, 2))  # Skewed high
            baseline_bp = float(rng.normal(135, 10))
            baseline_a1c = float(rng.normal(7.2, 1.0))
            housing_stability = float(rng.beta(5, 2))
            broadband_score = float(rng.beta(5, 2))
            english_proficiency = float(rng.beta(6, 2))
            prior_no_show_rate = float(rng.beta(2, 5))  # Skewed low
            device_sync_rate = float(rng.beta(5, 2))  # Skewed high
            sdoh_score = float(rng.beta(5, 2))  # Skewed high - advantaged zip codes

        # Assign chronic conditions based on complexity
        condition_probs = (
            [0.4, 0.5, 0.45, 0.35] if is_complex else [0.15, 0.2, 0.15, 0.2]
        )
        has_ckd = int(rng.random() < condition_probs[0])
        has_copd = int(rng.random() < condition_probs[1])
        has_hf = int(rng.random() < condition_probs[2])
        has_depression = int(rng.random() < condition_probs[3])

        # Clamp values to valid ranges
        engagement_score = np.clip(engagement_score, 0.0, 1.0)
        digital_literacy = np.clip(digital_literacy, 0.0, 1.0)
        housing_stability = np.clip(housing_stability, 0.0, 1.0)
        broadband_score = np.clip(broadband_score, 0.0, 1.0)
        english_proficiency = np.clip(english_proficiency, 0.0, 1.0)
        prior_no_show_rate = np.clip(prior_no_show_rate, 0.0, 1.0)
        device_sync_rate = np.clip(device_sync_rate, 0.0, 1.0)
        sdoh_score = np.clip(sdoh_score, 0.0, 1.0)
        baseline_bp = np.clip(baseline_bp, 90, 200)
        baseline_a1c = np.clip(baseline_a1c, 5.0, 14.0)

        # Initialize BP control outcome based on baseline BP
        # BP < 120: well controlled (~0.9)
        # BP 120-140: moderately controlled (~0.7)
        # BP 140-160: poorly controlled (~0.4)
        # BP > 160: uncontrolled (~0.2)
        if baseline_bp < 120:
            initial_outcome = float(rng.uniform(0.85, 0.95))
        elif baseline_bp < 140:
            initial_outcome = float(rng.uniform(0.6, 0.75))
        elif baseline_bp < 160:
            initial_outcome = float(rng.uniform(0.3, 0.5))
        else:
            initial_outcome = float(rng.uniform(0.1, 0.3))

        patient = Patient(
            id=i,
            true_complexity=true_complexity,
            age=age,
            num_chronic_conditions=num_conditions,
            has_ckd=has_ckd,
            has_copd=has_copd,
            has_hf=has_hf,
            has_depression=has_depression,
            baseline_bp=baseline_bp,
            baseline_a1c=baseline_a1c,
            engagement_score=engagement_score,
            prior_no_show_rate=prior_no_show_rate,
            device_sync_rate=device_sync_rate,
            housing_stability=housing_stability,
            broadband_score=broadband_score,
            english_proficiency=english_proficiency,
            sdoh_score=sdoh_score,
            digital_literacy=digital_literacy,
            initial_outcome=initial_outcome,
            current_outcome=initial_outcome,
        )
        patients.append(patient)

    return patients
