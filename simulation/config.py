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

    # Financial parameters (based on ACCESS model)
    # PMPM = $100, with $80 guaranteed floor and $20-40 earnback
    # Organization cost ~$60/month to serve patients
    base_pbpm: float = 80.0  # Guaranteed operating floor per month
    max_earnback_pbpm: float = 30.0  # Max earnback per month (avg $20-40 range)
    cost_per_patient: float = 720.0  # Annual cost per enrolled patient ($60/month)

    # Default policy thresholds
    default_min_engagement: float = 0.3
    default_max_conditions: int = 5
    default_min_digital_literacy: float = 0.2

    # AI optimization settings
    enable_ai_optimization: bool = True
    optimization_iterations: int = 50

    # Patient outcome parameters
    easy_improvement_prob: float = 0.6
    complex_improvement_prob: float = 0.2
    easy_improvement_min: float = 0.1
    easy_improvement_max: float = 0.2
    complex_improvement_min: float = 0.02
    complex_improvement_max: float = 0.08
