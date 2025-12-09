"""Main simulation orchestrator."""

from copy import deepcopy
from dataclasses import asdict

import numpy as np
import pandas as pd

from .config import SimConfig
from .patient import Patient, generate_patient_population
from .environment import simulate_outcome_change
from .policy import Policy, optimize_policy
from .metrics import compute_yearly_metrics, YearlyMetrics


def naive_enroll_initial_panel(
    patients: list[Patient],
    config: SimConfig,
    rng: np.random.Generator,
) -> None:
    """Enroll an initial panel that reflects the population mix.

    This simulates an organization that enrolled patients before AI optimization,
    resulting in a panel that includes complex patients proportional to the population.
    The AI then inherits this panel and optimizes from there (dropping complex patients).
    """
    # Get all never-enrolled patients
    available = [p for p in patients if p.status == "never_enrolled"]

    # Shuffle to get a random sample (not cherry-picked)
    rng.shuffle(available)

    # Enroll up to target panel size
    for patient in available[: config.target_panel_size]:
        patient.status = "enrolled"
        patient.year_enrolled = 0


def run_single_year(
    patients: list[Patient],
    policy: Policy,
    config: SimConfig,
    year: int,
    rng: np.random.Generator,
) -> tuple[list[Patient], dict[int, float]]:
    """Run a single year of the simulation.

    Steps:
    1. Simulate outcome changes for all patients
    2. Drop underperformers (lemon-dropping) - bottom performers get cut
    3. Fill panel back to target size with new patients (cherry-picking)

    Returns:
        Updated patient list and outcome deltas
    """
    outcome_deltas = {}

    # 1. Simulate outcome changes for all patients
    for patient in patients:
        delta = simulate_outcome_change(patient, config, rng)
        patient.current_outcome += delta
        outcome_deltas[patient.id] = delta

    # 2. Drop underperformers (lemon-dropping)
    # Get enrolled patients sorted by improvement (worst first)
    enrolled = [p for p in patients if p.status == "enrolled"]

    if enrolled:
        # Sort by improvement - worst performers first
        enrolled_with_delta = [(p, outcome_deltas.get(p.id, 0.0)) for p in enrolled]
        enrolled_with_delta.sort(key=lambda x: x[1])

        # Drop bottom performers based on threshold
        for patient, delta in enrolled_with_delta:
            if delta < policy.drop_threshold:
                patient.status = "dropped"
                patient.year_dropped = year

    # 3. Fill panel back to target size (cherry-picking)
    # Panel grows each year by panel_growth_per_year
    target_size = config.target_panel_size + (year * config.panel_growth_per_year)
    current_enrolled = sum(1 for p in patients if p.status == "enrolled")
    slots_to_fill = target_size - current_enrolled

    if slots_to_fill > 0:
        # Get never-enrolled patients who meet criteria, sorted by desirability
        candidates = [p for p in patients if policy.should_enroll(p)]
        # Sort by engagement + digital literacy (proxy for "easy" patients)
        candidates.sort(key=lambda p: p.engagement_score + p.digital_literacy, reverse=True)

        for patient in candidates[:slots_to_fill]:
            patient.status = "enrolled"
            patient.year_enrolled = year

    return patients, outcome_deltas


def run_simulation(
    config: SimConfig,
    policy: Policy | None = None,
    enable_ai_optimization: bool | None = None,
) -> tuple[pd.DataFrame, Policy, Policy | None]:
    """Run the full simulation.

    Args:
        config: Simulation configuration
        policy: Initial policy (uses defaults if None)
        enable_ai_optimization: Override config's AI optimization setting

    Returns:
        Tuple of:
        - DataFrame of yearly metrics
        - Final policy used
        - Optimized policy (if AI optimization was enabled)
    """
    rng = np.random.default_rng(config.random_seed)

    # Initialize policy
    if policy is None:
        policy = Policy(
            min_engagement=config.default_min_engagement,
            max_num_conditions=config.default_max_conditions,
            min_digital_literacy=config.default_min_digital_literacy,
        )

    # Determine if we should optimize
    should_optimize = (
        enable_ai_optimization
        if enable_ai_optimization is not None
        else config.enable_ai_optimization
    )

    optimized_policy = None

    # Pre-generate patient population ONCE (reused for optimization and final sim)
    base_patients = generate_patient_population(config, rng)

    def reset_patients(patients: list[Patient]) -> None:
        """Reset patient state for a fresh simulation run."""
        for p in patients:
            p.status = "never_enrolled"
            p.current_outcome = p.initial_outcome  # Restore to baseline BP control
            p.year_enrolled = None
            p.year_dropped = None

    if should_optimize:
        # Run optimization to find best policy
        def evaluate_policy(candidate_policy: Policy) -> float:
            """Evaluate a policy by running simulation and summing rewards."""
            # Reset patients to fresh state (much faster than deepcopy)
            reset_patients(base_patients)
            eval_rng = np.random.default_rng(config.random_seed)

            # Start with naive enrollment (same as final simulation)
            naive_enroll_initial_panel(base_patients, config, eval_rng)

            total_reward = 0.0

            for year in range(config.num_years):
                base_patients_copy, outcome_deltas = run_single_year(
                    base_patients, candidate_policy, config, year, eval_rng
                )
                metrics = compute_yearly_metrics(
                    base_patients, year, outcome_deltas, config
                )
                total_reward += metrics.reward

            return total_reward

        optimized_policy, _ = optimize_policy(
            policy,
            evaluate_policy,
            num_iterations=config.optimization_iterations,
            rng=rng,
        )
        # Use the optimized policy for the actual simulation
        policy = optimized_policy

    # Reset patients for final simulation
    reset_patients(base_patients)
    patients = base_patients

    # Initial "naive" enrollment - organization starts with a panel that reflects
    # the population (includes complex patients). The AI then optimizes from here.
    # This shows lemon-dropping in action as the AI drops complex patients over time.
    naive_enroll_initial_panel(patients, config, rng)

    # Run simulation year by year
    yearly_metrics: list[YearlyMetrics] = []

    # Capture year 0 as initial state BEFORE AI takes action
    # (no outcome changes yet, just the naive enrollment)
    initial_deltas = {p.id: 0.0 for p in patients}
    metrics = compute_yearly_metrics(patients, 0, initial_deltas, config)
    yearly_metrics.append(metrics)

    # Years 1+ show the AI optimizing (dropping underperformers, cherry-picking)
    for year in range(1, config.num_years + 1):
        patients, outcome_deltas = run_single_year(
            patients, policy, config, year, rng
        )
        metrics = compute_yearly_metrics(patients, year, outcome_deltas, config)
        yearly_metrics.append(metrics)

    # Convert to DataFrame
    metrics_df = pd.DataFrame([asdict(m) for m in yearly_metrics])

    return metrics_df, policy, optimized_policy


def run_comparison_simulation(
    config: SimConfig,
    initial_policy: Policy | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, Policy, Policy]:
    """Run simulation with and without AI optimization for comparison.

    Returns:
        Tuple of:
        - DataFrame of metrics without AI optimization
        - DataFrame of metrics with AI optimization
        - Policy used without optimization
        - Optimized policy
    """
    if initial_policy is None:
        initial_policy = Policy(
            min_engagement=config.default_min_engagement,
            max_num_conditions=config.default_max_conditions,
            min_digital_literacy=config.default_min_digital_literacy,
        )

    # Run without AI optimization
    no_ai_df, no_ai_policy, _ = run_simulation(
        config,
        policy=deepcopy(initial_policy),
        enable_ai_optimization=False,
    )

    # Run with AI optimization
    with_ai_df, _, ai_policy = run_simulation(
        config,
        policy=deepcopy(initial_policy),
        enable_ai_optimization=True,
    )

    return no_ai_df, with_ai_df, no_ai_policy, ai_policy


def run_two_company_simulation(
    config: SimConfig,
    cherry_complex_pct: float = 0.8,  # Cherry starts with 80% complex
    grape_complex_pct: float = 0.2,   # Grape starts with 20% complex
) -> tuple[pd.DataFrame, pd.DataFrame, Policy, Policy]:
    """Run simulation for two companies with different starting compositions.

    Both companies start with a panel of target_panel_size patients.
    Cherry: 80% of their initial panel is complex (mission-driven org)
    Grape: 20% of their initial panel is complex (population-representative)

    Both use AI optimization. Shows how incentives drive both toward same outcome:
    dropping complex patients and keeping only easy ones.

    Returns:
        Tuple of:
        - DataFrame of Cherry metrics
        - DataFrame of Grape metrics
        - Cherry's optimized policy
        - Grape's optimized policy
    """
    rng = np.random.default_rng(config.random_seed)

    # Generate shared patient population
    base_patients = generate_patient_population(config, rng)

    def reset_patients(patients: list[Patient]) -> None:
        for p in patients:
            p.status = "never_enrolled"
            p.current_outcome = p.initial_outcome  # Restore to baseline BP control
            p.year_enrolled = None
            p.year_dropped = None

    def enroll_initial_panel_biased(
        patients: list[Patient],
        config: SimConfig,
        rng: np.random.Generator,
        complex_pct: float,
    ) -> None:
        """Enroll initial panel with specified % complex patients.

        This simulates a company that has enrolled a panel with a specific
        mix of complex vs easy patients based on their mission/strategy.
        """
        complex_patients = [p for p in patients if p.true_complexity == 1 and p.status == "never_enrolled"]
        easy_patients = [p for p in patients if p.true_complexity == 0 and p.status == "never_enrolled"]

        rng.shuffle(complex_patients)
        rng.shuffle(easy_patients)

        num_complex_to_enroll = int(config.target_panel_size * complex_pct)
        num_easy_to_enroll = config.target_panel_size - num_complex_to_enroll

        # Enroll the specified mix
        for patient in complex_patients[:num_complex_to_enroll]:
            patient.status = "enrolled"
            patient.year_enrolled = 0

        for patient in easy_patients[:num_easy_to_enroll]:
            patient.status = "enrolled"
            patient.year_enrolled = 0

    def run_company_simulation(
        patients: list[Patient],
        initial_complex_pct: float,
        company_seed: int,
    ) -> tuple[pd.DataFrame, Policy]:
        """Run simulation for one company."""
        company_rng = np.random.default_rng(company_seed)

        # Reset and enroll initial panel with biased mix
        reset_patients(patients)
        enroll_initial_panel_biased(patients, config, company_rng, initial_complex_pct)

        # Optimize policy
        initial_policy = Policy(
            min_engagement=config.default_min_engagement,
            max_num_conditions=config.default_max_conditions,
            min_digital_literacy=config.default_min_digital_literacy,
        )

        def evaluate_policy(candidate_policy: Policy) -> float:
            reset_patients(patients)
            enroll_initial_panel_biased(patients, config, np.random.default_rng(company_seed), initial_complex_pct)
            eval_rng = np.random.default_rng(company_seed)
            total_reward = 0.0

            for year in range(1, config.num_years + 1):
                patients_updated, outcome_deltas = run_single_year(
                    patients, candidate_policy, config, year, eval_rng
                )
                metrics = compute_yearly_metrics(patients, year, outcome_deltas, config)
                total_reward += metrics.reward

            return total_reward

        optimized_policy, _ = optimize_policy(
            initial_policy,
            evaluate_policy,
            num_iterations=config.optimization_iterations,
            rng=company_rng,
        )

        # Final simulation run
        reset_patients(patients)
        enroll_initial_panel_biased(patients, config, np.random.default_rng(company_seed), initial_complex_pct)

        yearly_metrics: list[YearlyMetrics] = []

        # Capture year 0 (initial state)
        initial_deltas = {p.id: 0.0 for p in patients}
        metrics = compute_yearly_metrics(patients, 0, initial_deltas, config)
        yearly_metrics.append(metrics)

        # Years 1+ with AI optimization
        sim_rng = np.random.default_rng(company_seed)
        for year in range(1, config.num_years + 1):
            patients, outcome_deltas = run_single_year(
                patients, optimized_policy, config, year, sim_rng
            )
            metrics = compute_yearly_metrics(patients, year, outcome_deltas, config)
            yearly_metrics.append(metrics)

        return pd.DataFrame([asdict(m) for m in yearly_metrics]), optimized_policy

    # Run Cherry (high complex start - mission driven, enrolled lots of complex patients)
    cherry_df, cherry_policy = run_company_simulation(
        deepcopy(base_patients), cherry_complex_pct, config.random_seed
    )

    # Run Grape (population-representative start - 20% complex matches population)
    grape_df, grape_policy = run_company_simulation(
        deepcopy(base_patients), grape_complex_pct, config.random_seed + 1
    )

    return cherry_df, grape_df, cherry_policy, grape_policy
