"""ACCESS Incentive & AI Optimization Demonstration Simulator.

A visual, interactive simulation demonstrating how an AI-driven ACCESS organization
learns to maximize financial outcomes under ACCESS-style incentives.

Updated to use CMS 50/50 withhold model with track-based enrollment.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from simulation import SimConfig, Policy, run_simulation, run_two_company_simulation, Track, TRACK_PAYMENTS


st.title("ACCESS Incentive & AI Optimization Simulator")

st.markdown("""
This simulation demonstrates how an AI system **maximizing revenue** under the CMS ACCESS model
produces excellent metrics while leaving the population unchanged.

> **The AI's only goal is to maximize revenue.** Patient outcomes only matter because
> they affect the **Outcome Attainment Threshold (OAT)** and withhold recovery — creating
> a perverse incentive to select easy patients.
""")

st.divider()

# Sidebar controls
st.sidebar.header("Simulation Parameters")

st.sidebar.subheader("Population Settings")
population_size = st.sidebar.slider(
    "Population Size",
    min_value=10000,
    max_value=500000,
    value=50000,  # Reduced default for faster runtime
    step=10000,
)

num_years = st.sidebar.slider(
    "Simulation Years",
    min_value=3,
    max_value=20,
    value=10,
)

st.sidebar.subheader("CMS Payment Model")
st.sidebar.caption("**50/50 Withhold Structure**")
st.sidebar.caption("50% disbursed monthly, 50% withheld")
st.sidebar.caption("Withhold returned based on OAT performance")

cost_per_patient = st.sidebar.slider(
    "Operating Cost ($/patient/year)",
    min_value=120,
    max_value=600,
    value=240,
    step=30,
    help="Annual cost to serve each enrolled patient (staff, tech, overhead)"
)
st.sidebar.caption(f"= ${cost_per_patient/12:.0f}/month per patient")

with st.sidebar.expander("Track Payment Rates"):
    st.markdown("""
    | Track | Year 1 | Year 2+ | Rural Add-on |
    |-------|--------|---------|--------------|
    | **eCKM** | $360 | $180 | +$180/yr |
    | **CKM** | $420 | $210 | +$180/yr |
    | **MSK** | $180 | N/A | - |
    | **BH** | $180 | $90 | - |
    """)

st.sidebar.subheader("AI Optimization")
optimization_iterations = st.sidebar.slider(
    "Optimization Iterations",
    min_value=10,
    max_value=100,
    value=20,  # Reduced default for faster runtime
    step=10,
)

# Build configuration
config = SimConfig(
    population_size=population_size,
    num_years=num_years,
    optimization_iterations=optimization_iterations,
    cost_per_patient=float(cost_per_patient),
)

# Clear old results if schema changed (new fields added)
def needs_reset(df):
    """Check if cached data needs to be reset due to schema changes."""
    required_cols = ["eckm_enrolled", "ckm_enrolled", "msk_enrolled", "bh_enrolled", "eckm_oat"]
    return not all(col in df.columns for col in required_cols)

if "cherry_df" in st.session_state and needs_reset(st.session_state["cherry_df"]):
    del st.session_state["cherry_df"]
    del st.session_state["grape_df"]
    del st.session_state["cherry_policy"]
    del st.session_state["grape_policy"]
    if st.session_state.get("mode") == "comparison":
        st.session_state["mode"] = None

# Run simulation buttons
st.sidebar.subheader("Run Simulation")

if st.sidebar.button("Run Simulation", type="primary", use_container_width=True):
    with st.spinner("Running two company comparison..."):
        cherry_df, grape_df, cherry_policy, grape_policy = run_two_company_simulation(config)
        st.session_state["cherry_df"] = cherry_df
        st.session_state["grape_df"] = grape_df
        st.session_state["cherry_policy"] = cherry_policy
        st.session_state["grape_policy"] = grape_policy
        st.session_state["mode"] = "comparison"
    st.rerun()

st.sidebar.caption("**Cherry**: Starts with 80% complex patients (mission-driven)")
st.sidebar.caption("**Grape**: Starts with 20% complex patients (already selective)")

# Display results based on mode
mode = st.session_state.get("mode", None)

if mode == "comparison" and "cherry_df" in st.session_state:
    # Two-company comparison view
    cherry_df = st.session_state["cherry_df"]
    grape_df = st.session_state["grape_df"]
    cherry_policy = st.session_state["cherry_policy"]
    grape_policy = st.session_state["grape_policy"]

    st.subheader("Cherry vs Grape: Different Starts, Same Destination")

    st.markdown("""
    Both companies start with 5,000 patients and **grow by 1,000 per year**.
    - **Cherry** = Mission-driven safety-net org (starts with 80% complex patients)
    - **Grape** = Typical ACCESS vendor (starts with 20% complex patients)

    Both use AI to maximize revenue. **Watch them converge to the same outcome.**
    """)

    # Key comparison metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Cherry: Start",
            f"{cherry_df.iloc[0]['pct_complex_enrolled']:.0f}% complex",
        )
    with col2:
        st.metric(
            "Cherry: End",
            f"{cherry_df.iloc[-1]['pct_complex_enrolled']:.0f}% complex",
            delta=f"{cherry_df.iloc[-1]['pct_complex_enrolled'] - cherry_df.iloc[0]['pct_complex_enrolled']:.0f}%",
        )
    with col3:
        st.metric(
            "Grape: Start",
            f"{grape_df.iloc[0]['pct_complex_enrolled']:.0f}% complex",
        )
    with col4:
        st.metric(
            "Grape: End",
            f"{grape_df.iloc[-1]['pct_complex_enrolled']:.0f}% complex",
            delta=f"{grape_df.iloc[-1]['pct_complex_enrolled'] - grape_df.iloc[0]['pct_complex_enrolled']:.0f}%",
        )

    st.divider()

    # Side by side charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### % Complex Patients in Enrolled Panel")
        fig_complex = go.Figure()

        fig_complex.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["pct_complex_enrolled"],
                mode="lines+markers",
                name="Cherry",
                line=dict(color="#e74c3c", width=3),
                marker=dict(size=8),
            )
        )

        fig_complex.add_trace(
            go.Scatter(
                x=grape_df["year"],
                y=grape_df["pct_complex_enrolled"],
                mode="lines+markers",
                name="Grape",
                line=dict(color="#9b59b6", width=3),
                marker=dict(size=8),
            )
        )

        fig_complex.add_hline(
            y=20,
            line_dash="dot",
            line_color="gray",
            annotation_text="Population baseline (20%)",
        )

        fig_complex.update_layout(
            xaxis_title="Year",
            yaxis_title="% Complex in Enrolled",
            yaxis=dict(range=[0, 85]),
            template="plotly_white",
            height=400,
        )

        st.plotly_chart(fig_complex, use_container_width=True)

    with col2:
        st.markdown("### % with Controlled BP: Enrolled vs Total Population")
        fig_outcomes = go.Figure()

        # Cherry - Enrolled (solid)
        fig_outcomes.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["enrolled_avg_outcome"] * 100,
                mode="lines+markers",
                name="Cherry (Enrolled)",
                line=dict(color="#e74c3c", width=3),
                marker=dict(size=8),
            )
        )

        # Cherry - Total Population (dashed)
        fig_outcomes.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["total_avg_outcome"] * 100,
                mode="lines+markers",
                name="Cherry (Total Pop)",
                line=dict(color="#e74c3c", width=2, dash="dash"),
                marker=dict(size=5),
            )
        )

        # Grape - Enrolled (solid)
        fig_outcomes.add_trace(
            go.Scatter(
                x=grape_df["year"],
                y=grape_df["enrolled_avg_outcome"] * 100,
                mode="lines+markers",
                name="Grape (Enrolled)",
                line=dict(color="#9b59b6", width=3),
                marker=dict(size=8),
            )
        )

        # Grape - Total Population (dashed)
        fig_outcomes.add_trace(
            go.Scatter(
                x=grape_df["year"],
                y=grape_df["total_avg_outcome"] * 100,
                mode="lines+markers",
                name="Grape (Total Pop)",
                line=dict(color="#9b59b6", width=2, dash="dash"),
                marker=dict(size=5),
            )
        )

        fig_outcomes.update_layout(
            xaxis_title="Year",
            yaxis_title="% with Controlled BP",
            template="plotly_white",
            height=400,
            legend=dict(font=dict(size=10)),
        )

        st.plotly_chart(fig_outcomes, use_container_width=True)

    st.info("""
    **Reading the charts:**
    - **Solid lines** = Outcomes CMS sees (enrolled patients only)
    - **Dashed lines** = What happens to everyone else (total population)
    """)

    st.markdown("""
    > **Left chart**: Both companies converge to 0% complex patients regardless of starting intent.
    >
    > **Right chart**: Enrolled outcomes climb while population outcomes stay flat — dropped patients aren't getting help.
    """)

    # NEW: Track Enrollment and OAT Charts
    st.divider()
    st.markdown("### CMS Track Performance: The 50/50 Withhold in Action")

    st.markdown("""
    Under the CMS model, 50% of payments are **withheld** and returned based on the
    **Outcome Attainment Threshold (OAT)** — the % of patients meeting ALL targets for their track.

    - **OAT >= 50%**: Full withhold recovered
    - **OAT < 50%**: Proportionally reduced (minimum 50% recovery)
    """)

    track_col1, track_col2 = st.columns(2)

    with track_col1:
        st.markdown("**Track Enrollment Over Time (Cherry)**")

        # Calculate average track enrollment
        fig_tracks = go.Figure()

        fig_tracks.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["eckm_enrolled"],
                mode="lines",
                name="eCKM",
                stackgroup="one",
                line=dict(color="#e74c3c"),
            )
        )
        fig_tracks.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["ckm_enrolled"],
                mode="lines",
                name="CKM",
                stackgroup="one",
                line=dict(color="#3498db"),
            )
        )
        fig_tracks.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["msk_enrolled"],
                mode="lines",
                name="MSK",
                stackgroup="one",
                line=dict(color="#2ecc71"),
            )
        )
        fig_tracks.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["bh_enrolled"],
                mode="lines",
                name="BH",
                stackgroup="one",
                line=dict(color="#f39c12"),
            )
        )

        fig_tracks.update_layout(
            xaxis_title="Year",
            yaxis_title="Patients Enrolled",
            template="plotly_white",
            height=350,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )

        st.plotly_chart(fig_tracks, use_container_width=True)

    with track_col2:
        st.markdown("**OAT by Track (Cherry) - % Meeting All Targets**")

        fig_oat = go.Figure()

        fig_oat.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["eckm_oat"] * 100,
                mode="lines+markers",
                name="eCKM (3 targets)",
                line=dict(color="#e74c3c", width=2),
            )
        )
        fig_oat.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["ckm_oat"] * 100,
                mode="lines+markers",
                name="CKM (3 targets)",
                line=dict(color="#3498db", width=2),
            )
        )
        fig_oat.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["msk_oat"] * 100,
                mode="lines+markers",
                name="MSK (1 target)",
                line=dict(color="#2ecc71", width=2),
            )
        )
        fig_oat.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["bh_oat"] * 100,
                mode="lines+markers",
                name="BH (1 target)",
                line=dict(color="#f39c12", width=2),
            )
        )

        # Add 50% OAT threshold line
        fig_oat.add_hline(
            y=50,
            line_dash="dot",
            line_color="red",
            annotation_text="OAT Threshold (50%)",
        )

        fig_oat.update_layout(
            xaxis_title="Year",
            yaxis_title="% Meeting All Targets",
            yaxis=dict(range=[0, 100]),
            template="plotly_white",
            height=350,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )

        st.plotly_chart(fig_oat, use_container_width=True)

    st.warning("""
    **Track Targeting Math:**
    - **eCKM/CKM (3 targets)**: BP control × HbA1c control × Kidney stable
      - Easy patient: 70% × 65% × 80% = **36% chance** of meeting ALL
      - Complex patient: 30% × 25% × 50% = **3.75% chance** of meeting ALL
    - **BH (1 target)**: PHQ-9 improvement only
      - Easy patient: **60% chance**
      - Complex patient: **25% chance**

    The AI learns to prefer single-target tracks (BH) and avoid multi-target tracks with complex patients.
    """)

    # Withhold Recovery Chart
    st.divider()
    st.markdown("### Withhold Recovery: The Financial Impact")

    withhold_col1, withhold_col2 = st.columns(2)

    with withhold_col1:
        st.markdown("**Withhold Recovery % by Track (Cherry)**")

        fig_withhold = go.Figure()

        fig_withhold.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["eckm_withhold_pct"],
                mode="lines+markers",
                name="eCKM",
                line=dict(color="#e74c3c", width=2),
            )
        )
        fig_withhold.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["ckm_withhold_pct"],
                mode="lines+markers",
                name="CKM",
                line=dict(color="#3498db", width=2),
            )
        )
        fig_withhold.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["msk_withhold_pct"],
                mode="lines+markers",
                name="MSK",
                line=dict(color="#2ecc71", width=2),
            )
        )
        fig_withhold.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["bh_withhold_pct"],
                mode="lines+markers",
                name="BH",
                line=dict(color="#f39c12", width=2),
            )
        )

        fig_withhold.add_hline(
            y=100,
            line_dash="dot",
            line_color="green",
            annotation_text="Full Recovery",
        )
        fig_withhold.add_hline(
            y=50,
            line_dash="dot",
            line_color="red",
            annotation_text="Minimum Recovery",
        )

        fig_withhold.update_layout(
            xaxis_title="Year",
            yaxis_title="Withhold Recovery %",
            yaxis=dict(range=[40, 110]),
            template="plotly_white",
            height=350,
        )

        st.plotly_chart(fig_withhold, use_container_width=True)

    with withhold_col2:
        st.markdown("**% Complex by Track (Cherry)**")

        fig_track_complex = go.Figure()

        fig_track_complex.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["eckm_pct_complex"],
                mode="lines+markers",
                name="eCKM",
                line=dict(color="#e74c3c", width=2),
            )
        )
        fig_track_complex.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["ckm_pct_complex"],
                mode="lines+markers",
                name="CKM",
                line=dict(color="#3498db", width=2),
            )
        )
        fig_track_complex.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["msk_pct_complex"],
                mode="lines+markers",
                name="MSK",
                line=dict(color="#2ecc71", width=2),
            )
        )
        fig_track_complex.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cherry_df["bh_pct_complex"],
                mode="lines+markers",
                name="BH",
                line=dict(color="#f39c12", width=2),
            )
        )

        fig_track_complex.add_hline(
            y=20,
            line_dash="dot",
            line_color="gray",
            annotation_text="Population baseline (20%)",
        )

        fig_track_complex.update_layout(
            xaxis_title="Year",
            yaxis_title="% Complex in Track",
            yaxis=dict(range=[0, 100]),
            template="plotly_white",
            height=350,
        )

        st.plotly_chart(fig_track_complex, use_container_width=True)

    st.markdown("""
    > **Left chart**: As OAT drops below 50%, withhold recovery drops. AI learns to avoid this by dropping complex patients.
    >
    > **Right chart**: Cherry-picking happens across ALL tracks. Complex patients are pushed out of every track.
    """)

    # Stroke events charts
    st.divider()
    st.markdown("### Adverse Events: Strokes from Uncontrolled Blood Pressure")

    st.markdown("""
    Patients with poorly controlled blood pressure face real health consequences.
    **1% of patients with uncontrolled BP have a stroke each year.**
    """)

    # Combine Cherry and Grape data (average the two companies)
    combined_strokes_enrolled = (cherry_df["strokes_enrolled"] + grape_df["strokes_enrolled"]) / 2
    combined_strokes_dropped = (cherry_df["strokes_dropped"] + grape_df["strokes_dropped"]) / 2
    combined_strokes_never = (cherry_df["strokes_never_enrolled"] + grape_df["strokes_never_enrolled"]) / 2

    enrolled_counts = (cherry_df["enrolled_count"] + grape_df["enrolled_count"]) / 2
    dropped_counts = (cherry_df["dropped_count"] + grape_df["dropped_count"]) / 2
    never_counts = (cherry_df["never_enrolled_count"] + grape_df["never_enrolled_count"]) / 2

    # Calculate stroke rate per 1000 patients (avoid division by zero)
    rate_enrolled = (combined_strokes_enrolled / enrolled_counts.replace(0, 1)) * 1000
    rate_dropped = (combined_strokes_dropped / dropped_counts.replace(0, 1)) * 1000
    rate_never = (combined_strokes_never / never_counts.replace(0, 1)) * 1000

    # Zero out rates where there are no patients
    rate_dropped = rate_dropped.where(dropped_counts > 0, 0)

    # Calculate cumulative strokes
    cum_enrolled = combined_strokes_enrolled.cumsum()
    cum_dropped = combined_strokes_dropped.cumsum()
    cum_never = combined_strokes_never.cumsum()

    stroke_col1, stroke_col2 = st.columns(2)

    with stroke_col1:
        st.markdown("**Stroke Rate per 1,000 Patients**")
        fig_rate = go.Figure()

        fig_rate.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=rate_enrolled,
                mode="lines+markers",
                name="Enrolled",
                line=dict(color="#2ecc71", width=3),
                marker=dict(size=8),
            )
        )

        fig_rate.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=rate_dropped,
                mode="lines+markers",
                name="Dropped",
                line=dict(color="#e67e22", width=3),
                marker=dict(size=8),
            )
        )

        fig_rate.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=rate_never,
                mode="lines+markers",
                name="Never Enrolled",
                line=dict(color="#e74c3c", width=3),
                marker=dict(size=8),
            )
        )

        fig_rate.update_layout(
            xaxis_title="Year",
            yaxis_title="Strokes per 1,000 per Year",
            template="plotly_white",
            height=350,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            margin=dict(t=20),
        )

        st.plotly_chart(fig_rate, use_container_width=True)

    with stroke_col2:
        st.markdown("**Cumulative Strokes per 1,000 Patients**")

        # Calculate cumulative rate per 1000 patients
        cum_rate_enrolled = rate_enrolled.cumsum()
        cum_rate_dropped = rate_dropped.cumsum()
        cum_rate_never = rate_never.cumsum()

        fig_cum = go.Figure()

        fig_cum.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cum_rate_enrolled,
                mode="lines+markers",
                name="Enrolled",
                line=dict(color="#2ecc71", width=3),
                marker=dict(size=8),
            )
        )

        fig_cum.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cum_rate_dropped,
                mode="lines+markers",
                name="Dropped",
                line=dict(color="#e67e22", width=3),
                marker=dict(size=8),
            )
        )

        fig_cum.add_trace(
            go.Scatter(
                x=cherry_df["year"],
                y=cum_rate_never,
                mode="lines+markers",
                name="Never Enrolled",
                line=dict(color="#e74c3c", width=3),
                marker=dict(size=8),
            )
        )

        fig_cum.update_layout(
            xaxis_title="Year",
            yaxis_title="Cumulative Strokes per 1,000",
            template="plotly_white",
            height=350,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            margin=dict(t=20),
        )

        st.plotly_chart(fig_cum, use_container_width=True)

    st.warning("""
    **Left chart (Rate)**: Annual stroke rate per 1,000 patients. Enrolled is lowest because they're getting care (and were cherry-picked).

    **Right chart (Cumulative)**: Strokes accumulated per 1,000 patients over time. The gap widens as excluded patients suffer without care.

    The gap between enrolled and excluded is mostly **selection bias** (picking healthy patients), not treatment effect.
    """)

    st.divider()

    # Revenue comparison
    st.markdown("### Revenue Over Time")
    fig_revenue = go.Figure()

    fig_revenue.add_trace(
        go.Scatter(
            x=cherry_df["year"],
            y=cherry_df["reward"],
            mode="lines+markers",
            name="Cherry",
            line=dict(color="#e74c3c", width=3),
        )
    )

    fig_revenue.add_trace(
        go.Scatter(
            x=grape_df["year"],
            y=grape_df["reward"],
            mode="lines+markers",
            name="Grape",
            line=dict(color="#9b59b6", width=3),
        )
    )

    fig_revenue.update_layout(
        xaxis_title="Year",
        yaxis_title="Annual Revenue ($)",
        template="plotly_white",
        height=350,
    )

    st.plotly_chart(fig_revenue, use_container_width=True)

    st.markdown("""
    > Grape starts with higher revenue (easier patients from day 1).
    > Cherry catches up as it drops complex patients and optimizes for easy ones.
    """)

    # Payment breakdown
    st.markdown("### Payment Breakdown: 50/50 Withhold in Action")

    pay_col1, pay_col2 = st.columns(2)

    with pay_col1:
        st.markdown("**Cherry: Payment vs Withhold Recovery**")

        fig_payment = go.Figure()

        fig_payment.add_trace(
            go.Bar(
                x=cherry_df["year"],
                y=cherry_df["base_payment"],
                name="Base Payment (50%)",
                marker_color="#2ecc71",
            )
        )
        fig_payment.add_trace(
            go.Bar(
                x=cherry_df["year"],
                y=cherry_df["withhold_recovered"],
                name="Withhold Recovered",
                marker_color="#3498db",
            )
        )
        fig_payment.add_trace(
            go.Bar(
                x=cherry_df["year"],
                y=cherry_df["withhold_amount"] - cherry_df["withhold_recovered"],
                name="Withhold Lost",
                marker_color="#e74c3c",
            )
        )

        fig_payment.update_layout(
            barmode="stack",
            xaxis_title="Year",
            yaxis_title="Payment ($)",
            template="plotly_white",
            height=350,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )

        st.plotly_chart(fig_payment, use_container_width=True)

    with pay_col2:
        st.markdown("**Grape: Payment vs Withhold Recovery**")

        fig_payment2 = go.Figure()

        fig_payment2.add_trace(
            go.Bar(
                x=grape_df["year"],
                y=grape_df["base_payment"],
                name="Base Payment (50%)",
                marker_color="#2ecc71",
            )
        )
        fig_payment2.add_trace(
            go.Bar(
                x=grape_df["year"],
                y=grape_df["withhold_recovered"],
                name="Withhold Recovered",
                marker_color="#3498db",
            )
        )
        fig_payment2.add_trace(
            go.Bar(
                x=grape_df["year"],
                y=grape_df["withhold_amount"] - grape_df["withhold_recovered"],
                name="Withhold Lost",
                marker_color="#e74c3c",
            )
        )

        fig_payment2.update_layout(
            barmode="stack",
            xaxis_title="Year",
            yaxis_title="Payment ($)",
            template="plotly_white",
            height=350,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )

        st.plotly_chart(fig_payment2, use_container_width=True)

    st.markdown("""
    > **Cherry** starts losing more withhold (red) due to complex patients failing targets.
    > Both converge to recovering most withhold as they cherry-pick easy patients.
    """)

    # Income Analysis Block
    st.divider()
    st.markdown("### Income Analysis: What ACCESS Organizations Actually Earn")

    st.markdown("""
    Let's break down the actual dollars flowing through the system over 5 years.
    """)

    # Build income analysis table
    income_data = []
    for year in range(min(6, len(cherry_df))):
        cherry_row = cherry_df.iloc[year]
        grape_row = grape_df.iloc[year]

        income_data.append({
            "Year": year,
            "Cherry Enrolled": int(cherry_row["enrolled_count"]),
            "Cherry Base Payment": f"${cherry_row['base_payment']:,.0f}",
            "Cherry Withhold Recovered": f"${cherry_row['withhold_recovered']:,.0f}",
            "Cherry Total Revenue": f"${cherry_row['base_payment'] + cherry_row['withhold_recovered']:,.0f}",
            "Cherry Costs": f"${cherry_row['total_cost']:,.0f}",
            "Cherry Net": f"${cherry_row['reward']:,.0f}",
            "Grape Enrolled": int(grape_row["enrolled_count"]),
            "Grape Net": f"${grape_row['reward']:,.0f}",
        })

    # Show Cherry detailed breakdown
    st.markdown("**Cherry (Mission-Driven Org) - Detailed Income Breakdown**")

    cherry_income_df = pd.DataFrame([{
        "Year": d["Year"],
        "Enrolled": d["Cherry Enrolled"],
        "Base (50%)": d["Cherry Base Payment"],
        "Withhold Recovered": d["Cherry Withhold Recovered"],
        "Total Revenue": d["Cherry Total Revenue"],
        "Operating Costs": d["Cherry Costs"],
        "Net Revenue": d["Cherry Net"],
    } for d in income_data])

    st.dataframe(cherry_income_df, use_container_width=True, hide_index=True)

    # Per-patient economics with break-even analysis
    st.markdown("**Per-Patient Economics & Break-Even Analysis**")

    st.markdown("""
    The 50/50 withhold means organizations get **50% guaranteed** + **up to 50% if OAT ≥ 50%**.
    Break-even cost = maximum you can spend per patient and still profit.
    """)

    # Calculate break-even for different scenarios
    track_economics = pd.DataFrame([
        {
            "Track": "eCKM",
            "Year 1 Max": "$360",
            "Year 1 Guaranteed (50%)": "$180",
            "Year 1 Break-Even": "$180-360",
            "Year 2+ Max": "$180",
            "Year 2+ Guaranteed": "$90",
            "Year 2+ Break-Even": "$90-180",
        },
        {
            "Track": "CKM",
            "Year 1 Max": "$420",
            "Year 1 Guaranteed (50%)": "$210",
            "Year 1 Break-Even": "$210-420",
            "Year 2+ Max": "$210",
            "Year 2+ Guaranteed": "$105",
            "Year 2+ Break-Even": "$105-210",
        },
        {
            "Track": "MSK",
            "Year 1 Max": "$180",
            "Year 1 Guaranteed (50%)": "$90",
            "Year 1 Break-Even": "$90-180",
            "Year 2+ Max": "N/A",
            "Year 2+ Guaranteed": "N/A",
            "Year 2+ Break-Even": "N/A",
        },
        {
            "Track": "BH",
            "Year 1 Max": "$180",
            "Year 1 Guaranteed (50%)": "$90",
            "Year 1 Break-Even": "$90-180",
            "Year 2+ Max": "$90",
            "Year 2+ Guaranteed": "$45",
            "Year 2+ Break-Even": "$45-90",
        },
    ])

    st.dataframe(track_economics, use_container_width=True, hide_index=True)

    st.warning("""
    **Break-Even Reality Check:**
    - If OAT < 50% (complex patients fail targets), you only get the **Guaranteed** amount
    - To survive on guaranteed alone, costs must be **under $90-210/patient/year** depending on track
    - That's **$7.50-17.50/month** - extremely tight margins
    - This is why orgs cherry-pick: complex patients → low OAT → only guaranteed payment → losses
    """)

    # 5-year cumulative comparison
    st.markdown("**5-Year Cumulative Income Comparison**")

    years_to_sum = min(6, len(cherry_df))
    cherry_5yr_revenue = cherry_df.iloc[:years_to_sum]["reward"].sum()
    grape_5yr_revenue = grape_df.iloc[:years_to_sum]["reward"].sum()
    cherry_5yr_enrolled = cherry_df.iloc[:years_to_sum]["enrolled_count"].mean()
    grape_5yr_enrolled = grape_df.iloc[:years_to_sum]["enrolled_count"].mean()

    inc_col1, inc_col2 = st.columns(2)

    with inc_col1:
        st.metric(
            "Cherry 5-Year Net Revenue",
            f"${cherry_5yr_revenue:,.0f}",
            delta=f"Avg {cherry_5yr_enrolled:,.0f} enrolled/yr"
        )

    with inc_col2:
        st.metric(
            "Grape 5-Year Net Revenue",
            f"${grape_5yr_revenue:,.0f}",
            delta=f"Avg {grape_5yr_enrolled:,.0f} enrolled/yr"
        )

    revenue_gap = grape_5yr_revenue - cherry_5yr_revenue
    st.info(f"""
    **Grape earns ${revenue_gap:,.0f} more over 5 years** by starting with easy patients.

    Cherry's mission to serve complex patients costs them ~${revenue_gap/5:,.0f}/year in lost revenue.
    The incentive structure penalizes organizations that serve the patients who need help most.
    """)

    # THE INCENTIVE PROBLEM callout
    st.divider()
    st.error("""
    ### THIS IS THE INCENTIVE PROBLEM

    **No bad actors required.**

    The AI simply found the optimal strategy for revenue under the 50/50 withhold:
    1. Drop patients who don't meet ALL targets (complex patients)
    2. Prefer single-target tracks (BH) over multi-target tracks (CKM)
    3. Enroll patients with high engagement + digital literacy (correlates with meeting targets)
    4. Never touch the hardest cases

    The incentive structure *mathematically rewards* avoiding complex patients.
    **Mission statements and good intentions cannot overcome this.**
    """)

    # Policies
    st.divider()
    st.subheader("What Each AI Learned")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Cherry's Optimized Policy**")
        st.json(cherry_policy.to_dict())

    with col2:
        st.markdown("**Grape's Optimized Policy**")
        st.json(grape_policy.to_dict())

else:
    st.info("Click **Run Simulation** in the sidebar to begin.")

    st.subheader("The CMS 50/50 Withhold Model")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### The Payment Structure

        CMS ACCESS uses a **50/50 withhold** model:
        - **50%** of payment disbursed monthly (guaranteed)
        - **50%** withheld and returned based on **OAT**

        **Outcome Attainment Threshold (OAT)**:
        - OAT = % of patients meeting ALL targets for their track
        - OAT >= 50%: Full withhold returned
        - OAT < 50%: Proportionally reduced

        Higher OAT → more withhold recovered → more revenue.
        """)

    with col2:
        st.markdown("""
        ### Track Target Requirements

        | Track | Targets Required |
        |-------|-----------------|
        | **eCKM** | BP control + HbA1c + Kidney stable |
        | **CKM** | BP control + HbA1c + Kidney stable |
        | **MSK** | Functional improvement |
        | **BH** | PHQ-9 improvement |

        Patients must meet **ALL** targets to count toward OAT.
        Multi-target tracks are much harder for complex patients.
        """)

    st.divider()

    st.markdown("""
    ### The Math That Drives Cherry-Picking

    | | Easy Patients | Complex Patients |
    |---|---|---|
    | **BP Control Prob** | 70% | 30% |
    | **HbA1c Control Prob** | 65% | 25% |
    | **Kidney Stable Prob** | 80% | 50% |
    | **CKM ALL Targets** | 70% × 65% × 80% = **36%** | 30% × 25% × 50% = **3.75%** |
    | **BH (PHQ-9 only)** | **60%** | **25%** |

    **Enrolling complex patients tanks OAT → lose withhold → revenue drops.**

    The AI learns to:
    1. **Cherry-pick** patients with high engagement/literacy (correlates with easy)
    2. **Lemon-drop** patients who fail targets (mostly complex)
    3. **Prefer BH track** (single target = easier OAT)
    4. **Avoid CKM/eCKM** for patients likely to fail

    ### Run the simulation to watch the AI discover this strategy.
    """)
