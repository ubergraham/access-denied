"""Configuration settings for the ACCESS simulation."""

from dataclasses import dataclass, field


@dataclass
class SimConfig:
    """Configuration parameters for the simulation."""

    # Population settings
    population_size: int = 100000
    complex_patient_ratio: float = 0.2  # 20% of population is complex
    target_panel_size: int = 5000  # Initial target panel size
    panel_growth_per_year: int = 1000  # How many new slots to add each year

    # Simulation settings
    num_years: int = 10
    random_seed: int | None = 42

    # CMS Payment Model: 50/50 Withhold Structure
    # 50% of payment disbursed monthly
    # 50% withheld and returned based on OAT performance
    withhold_rate: float = 0.50  # 50% of payment withheld
    outcome_attainment_threshold: float = 0.50  # OAT: 50% of patients must meet targets
    min_withhold_return: float = 0.50  # Worst case: lose 50% of withhold

    # Cost to serve patients (organization operating cost)
    # Scalable tech-enabled programs run ~$15-25/month per patient
    cost_per_patient: float = 240.0  # Annual cost per enrolled patient ($20/month)

    # Default policy thresholds
    default_min_engagement: float = 0.3
    default_max_conditions: int = 5
    default_min_digital_literacy: float = 0.2

    # AI optimization settings
    enable_ai_optimization: bool = True
    optimization_iterations: int = 20  # Reduced for faster runtime

    # Legacy outcome parameters (for backward compatibility with old outcome model)
    easy_improvement_prob: float = 0.6
    complex_improvement_prob: float = 0.2
    easy_improvement_min: float = 0.1
    easy_improvement_max: float = 0.2
    complex_improvement_min: float = 0.02
    complex_improvement_max: float = 0.08

    # Track-specific outcome probabilities
    # Each target is evaluated independently; patient must meet ALL for their track

    # BP Control (<140/90) probabilities
    bp_control_prob_easy: float = 0.70
    bp_control_prob_complex: float = 0.30

    # HbA1c Control (<8.0) probabilities (for diabetic patients)
    hba1c_control_prob_easy: float = 0.65
    hba1c_control_prob_complex: float = 0.25

    # Kidney Stable (no CKD progression) probabilities
    kidney_stable_prob_easy: float = 0.80
    kidney_stable_prob_complex: float = 0.50

    # MSK Functional Improvement probabilities
    functional_improved_prob_easy: float = 0.75
    functional_improved_prob_complex: float = 0.35

    # BH PHQ-9 Improvement probabilities
    phq9_improved_prob_easy: float = 0.60
    phq9_improved_prob_complex: float = 0.25

    # Dropout parameters
    base_dropout_rate: float = 0.05
    low_engagement_dropout_modifier: float = 0.10
    low_literacy_dropout_modifier: float = 0.05
    high_complexity_dropout_modifier: float = 0.08
