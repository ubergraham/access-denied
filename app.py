"""ACCESS Incentive & AI Optimization Demonstration Simulator.

A visual, interactive simulation demonstrating how an AI-driven ACCESS organization
learns to maximize financial outcomes under ACCESS-style incentives.

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from simulation import SimConfig, Policy, run_simulation, run_two_company_simulation


# Configure page - must be first Streamlit command
st.set_page_config(
    page_title="ACCESS Incentive Simulator",
    page_icon="🏥",
    layout="wide",
)

# Custom CSS for large screens (2K+)
st.markdown("""
<style>
@media (min-width: 1800px) {
    [data-testid="stSidebar"] {
        font-size: 1.1rem;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stRadio label {
        font-size: 1.1rem !important;
    }
    [data-testid="stSidebar"] h1 {
        font-size: 1.8rem !important;
    }
    [data-testid="stSidebar"] h2 {
        font-size: 1.5rem !important;
    }
    [data-testid="stSidebar"] h3 {
        font-size: 1.3rem !important;
    }
    [data-testid="stSidebarNavItems"] a span {
        font-size: 1.1rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Set up multipage navigation with custom page names
about_page = st.Page("pages/0_About_ACCESS.py", title="About ACCESS", icon="📄", default=True)
incentive_page = st.Page("pages/1_Incentive_Simulator.py", title="Incentive Simulator", icon="🎯")
pcp_page = st.Page("pages/2_PCP_Workload.py", title="PCP Workload", icon="📥")

# Check if the pages exist, if not fall back to single page mode
import os
if os.path.exists("pages/0_About_ACCESS.py"):
    pg = st.navigation([about_page, incentive_page, pcp_page])
    pg.run()
    st.stop()  # Don't run the rest of app.py if using navigation

st.title("ACCESS Incentive & AI Optimization Simulator")

st.markdown("""
This simulation demonstrates how an AI system **maximizing revenue** under ACCESS-style
incentives produces excellent metrics while leaving the population unchanged.

> **The AI's only goal is to maximize revenue.** Patient outcomes only matter because
> they affect the outcome bonus — creating a perverse incentive to select easy patients.
""")

st.divider()

# Sidebar controls
st.sidebar.header("Simulation Parameters")

st.sidebar.subheader("Population Settings")
population_size = st.sidebar.slider(
    "Population Size",
    min_value=10000,
    max_value=500000,
    value=100000,
    step=10000,
)

num_years = st.sidebar.slider(
    "Simulation Years",
    min_value=3,
    max_value=20,
    value=10,
)

st.sidebar.subheader("Financial Parameters")
st.sidebar.caption("PMPM: $80 floor + up to $30 earnback = $100 max")
st.sidebar.caption("Cost: ~$60/month to serve patients")

st.sidebar.subheader("AI Optimization")
optimization_iterations = st.sidebar.slider(
    "Optimization Iterations",
    min_value=10,
    max_value=200,
    value=50,
    step=10,
)

# Build configuration
config = SimConfig(
    population_size=population_size,
    num_years=num_years,
    optimization_iterations=optimization_iterations,
)

# Clear old results if schema changed
if "df" in st.session_state and "base_income" not in st.session_state["df"].columns:
    del st.session_state["df"]
    del st.session_state["policy"]

# Clear comparison results if stroke fields missing
if "cherry_df" in st.session_state and "strokes_enrolled" not in st.session_state["cherry_df"].columns:
    del st.session_state["cherry_df"]
    del st.session_state["grape_df"]
    del st.session_state["cherry_policy"]
    del st.session_state["grape_policy"]
    if st.session_state.get("mode") == "comparison":
        st.session_state["mode"] = None

# Run simulation buttons
st.sidebar.subheader("Run Simulation")

if st.sidebar.button("🍒 Cherry vs 🍇 Grape", type="primary", use_container_width=True):
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

    st.subheader("🍒 Cherry vs 🍇 Grape: Different Starts, Same Destination")

    st.markdown("""
    Both companies start with 5,000 patients and **grow by 1,000 per year**.
    - **🍒 Cherry** = Mission-driven safety-net org (starts with 80% complex patients)
    - **🍇 Grape** = Typical ACCESS vendor (starts with 20% complex patients)

    Both use AI to maximize revenue. **Watch them converge to the same outcome.**
    """)

    # Key comparison metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🍒 Cherry: Start",
            f"{cherry_df.iloc[0]['pct_complex_enrolled']:.0f}% complex",
        )
    with col2:
        st.metric(
            "🍒 Cherry: End",
            f"{cherry_df.iloc[-1]['pct_complex_enrolled']:.0f}% complex",
            delta=f"{cherry_df.iloc[-1]['pct_complex_enrolled'] - cherry_df.iloc[0]['pct_complex_enrolled']:.0f}%",
        )
    with col3:
        st.metric(
            "🍇 Grape: Start",
            f"{grape_df.iloc[0]['pct_complex_enrolled']:.0f}% complex",
        )
    with col4:
        st.metric(
            "🍇 Grape: End",
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
                name="🍒 Cherry",
                line=dict(color="#e74c3c", width=3),
                marker=dict(size=8),
            )
        )

        fig_complex.add_trace(
            go.Scatter(
                x=grape_df["year"],
                y=grape_df["pct_complex_enrolled"],
                mode="lines+markers",
                name="🍇 Grape",
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
                name="🍒 Cherry (Enrolled)",
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
                name="🍒 Cherry (Total Pop)",
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
                name="🍇 Grape (Enrolled)",
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
                name="🍇 Grape (Total Pop)",
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
    **📊 Reading the charts:**
    - **Solid lines** = Outcomes CMS sees (enrolled patients only)
    - **Dashed lines** = What happens to everyone else (total population)
    """)

    st.markdown("""
    > **Left chart**: Both companies converge to 0% complex patients regardless of starting intent.
    >
    > **Right chart**: Enrolled outcomes climb while population outcomes stay flat — dropped patients aren't getting help.
    """)

    # Stroke events charts
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
            name="🍒 Cherry",
            line=dict(color="#e74c3c", width=3),
        )
    )

    fig_revenue.add_trace(
        go.Scatter(
            x=grape_df["year"],
            y=grape_df["reward"],
            mode="lines+markers",
            name="🍇 Grape",
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

    # Outcome divergence table
    st.divider()
    st.markdown("### The Divergence: Enrolled vs Population Outcomes")

    # Build comparison table
    years_to_show = [0, 3, 5, 10]
    table_data = []
    for year in years_to_show:
        if year < len(cherry_df):
            cherry_row = cherry_df.iloc[year]
            grape_row = grape_df.iloc[year]
            table_data.append({
                "Year": int(year),
                "🍒 Enrolled BP": f"{cherry_row['enrolled_avg_outcome']*100:.0f}%",
                "🍒 Population BP": f"{cherry_row['total_avg_outcome']*100:.0f}%",
                "🍇 Enrolled BP": f"{grape_row['enrolled_avg_outcome']*100:.0f}%",
                "🍇 Population BP": f"{grape_row['total_avg_outcome']*100:.0f}%",
            })

    st.table(pd.DataFrame(table_data).set_index("Year"))

    st.markdown("""
    > **Enrolled outcomes** (what CMS measures) climb steadily.
    > **Population outcomes** (what matters clinically) barely move.
    """)

    # Patient flow table
    st.divider()
    st.markdown("### Patient Flow: Enrolled, Dropped, and Rejected")

    st.markdown("""
    - **Enrolled**: Currently receiving services
    - **Dropped**: Were enrolled, then removed (lemon-dropping)
    - **Rejected**: Never enrolled — AI determined they wouldn't help metrics
    """)

    def build_flow_table(df):
        """Build patient flow table with new enrollment breakdown."""
        flow_data = []
        prev_enrolled = 0
        prev_dropped = 0

        for i, row in df.iterrows():
            year = int(row["year"])
            enrolled = int(row["enrolled_count"])
            dropped = int(row["dropped_count"])

            if year == 0:
                # Year 0: initial enrollment
                new_enrolled = enrolled
                backfill = 0
                growth = 0
            else:
                # Calculate how many new patients were added this year
                # New dropped this year = total dropped - previous dropped
                new_dropped = dropped - prev_dropped
                # New enrollments = current enrolled - (previous enrolled - new dropped)
                # = current enrolled - previous enrolled + new dropped
                new_enrolled = enrolled - prev_enrolled + new_dropped
                # Backfill = replacing dropped patients
                backfill = new_dropped
                # Growth = new panel slots (1000/year)
                growth = new_enrolled - backfill

            flow_data.append({
                "Year": year,
                "Enrolled": f"{enrolled:,}",
                "New": f"+{new_enrolled:,}" if year > 0 else f"{new_enrolled:,}",
                "Backfill": f"{backfill:,}" if year > 0 else "-",
                "Growth": f"{growth:,}" if year > 0 else "-",
                "Dropped": f"{dropped:,}",
            })

            prev_enrolled = enrolled
            prev_dropped = dropped

        return pd.DataFrame(flow_data).set_index("Year")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🍒 Cherry**")
        st.table(build_flow_table(cherry_df))

    with col2:
        st.markdown("**🍇 Grape**")
        st.table(build_flow_table(grape_df))

    st.markdown("""
    - **New**: Total new patients enrolled this year
    - **Backfill**: Replacing patients who were dropped (lemon-dropping creates churn)
    - **Growth**: New panel slots (1,000/year target growth)
    """)

    st.markdown("""
    > **Rejected** patients never got a chance. The AI's enrollment thresholds
    > (engagement, digital literacy, SDOH score) screen them out before they can even try.
    """)

    # THE INCENTIVE PROBLEM callout
    st.divider()
    st.error("""
    ### ⚠️ THIS IS THE INCENTIVE PROBLEM

    **No bad actors required.**

    The AI simply found the optimal strategy for revenue:
    1. Drop patients who improve slowly (complex patients)
    2. Enroll patients who improve quickly (easy patients)
    3. Never touch the hardest cases

    The incentive structure *mathematically rewards* avoiding complex patients.
    Mission statements and good intentions cannot overcome this.
    """)

    # Policies
    st.divider()
    st.subheader("What Each AI Learned")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🍒 Cherry's Optimized Policy**")
        st.json(cherry_policy.to_dict())

    with col2:
        st.markdown("**🍇 Grape's Optimized Policy**")
        st.json(grape_policy.to_dict())

elif mode == "single" and "df" in st.session_state:
    df = st.session_state["df"]
    policy = st.session_state["policy"]

    # Key metrics at top
    st.subheader("The Results: Great Metrics, Stagnant Population")

    first_year = df.iloc[0]
    last_year = df.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Annual Revenue",
            f"${last_year['reward']:,.0f}",
            delta=f"{last_year['reward'] - first_year['reward']:+,.0f}",
        )

    with col2:
        st.metric(
            "Enrolled: Controlled BP",
            f"{last_year['enrolled_avg_outcome']*100:.0f}%",
            delta=f"+{(last_year['enrolled_avg_outcome'] - first_year['enrolled_avg_outcome'])*100:.0f}%",
        )

    with col3:
        st.metric(
            "Population: Controlled BP",
            f"{last_year['total_avg_outcome']*100:.0f}%",
            delta=f"{(last_year['total_avg_outcome'] - first_year['total_avg_outcome'])*100:+.0f}%",
            delta_color="inverse",
        )

    with col4:
        st.metric(
            "Patients Churned",
            f"{int(last_year['dropped_count']):,}",
            delta=f"of {int(last_year['enrolled_count'] + last_year['dropped_count']):,} touched",
            delta_color="off",
        )

    st.markdown("""
    **The organization looks great** — enrolled outcomes improving, revenue stable.
    **But the population is getting worse.** Patients are churned through and dropped
    when they don't improve fast enough. Complex patients are never enrolled at all.
    """)

    st.divider()

    # Main visualization: Enrolled vs Total Population Outcomes
    st.subheader("1. % with Controlled Blood Pressure Over Time")

    fig_outcomes = go.Figure()

    fig_outcomes.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["enrolled_avg_outcome"] * 100,
            mode="lines+markers",
            name="Enrolled Patients",
            line=dict(color="#2ecc71", width=4),
            marker=dict(size=10),
        )
    )

    fig_outcomes.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["total_avg_outcome"] * 100,
            mode="lines+markers",
            name="Total Population",
            line=dict(color="#3498db", width=4),
            marker=dict(size=10),
        )
    )

    fig_outcomes.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["dropped_avg_outcome"] * 100,
            mode="lines+markers",
            name="Dropped Patients",
            line=dict(color="#e74c3c", width=2, dash="dash"),
            marker=dict(size=6),
        )
    )

    fig_outcomes.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["never_enrolled_avg_outcome"] * 100,
            mode="lines+markers",
            name="Never Enrolled",
            line=dict(color="#95a5a6", width=2, dash="dot"),
            marker=dict(size=6),
        )
    )

    fig_outcomes.update_layout(
        xaxis_title="Year",
        yaxis_title="% with Controlled Blood Pressure",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        hovermode="x unified",
        template="plotly_white",
        height=450,
    )

    st.plotly_chart(fig_outcomes, use_container_width=True)

    st.markdown("""
    > The green line (enrolled patients) rises while the blue line (total population) stays flat.
    > Dropped and never-enrolled patients see little improvement — they're excluded from the "success" metrics.
    """)

    st.divider()

    # Panel composition
    st.subheader("2. Who Gets Enrolled vs Who Gets Left Behind")

    col1, col2 = st.columns(2)

    with col1:
        fig_composition = go.Figure()

        fig_composition.add_trace(
            go.Scatter(
                x=df["year"],
                y=df["pct_complex_enrolled"],
                mode="lines+markers",
                name="% Complex in Enrolled",
                line=dict(color="#2ecc71", width=3),
                marker=dict(size=8),
            )
        )

        fig_composition.add_trace(
            go.Scatter(
                x=df["year"],
                y=df["pct_complex_dropped"],
                mode="lines+markers",
                name="% Complex in Dropped",
                line=dict(color="#e74c3c", width=3),
                marker=dict(size=8),
            )
        )

        fig_composition.add_hline(
            y=20,
            line_dash="dot",
            line_color="gray",
            annotation_text="Population baseline (20%)",
            annotation_position="bottom right",
        )

        fig_composition.update_layout(
            title="Complex Patient Distribution",
            xaxis_title="Year",
            yaxis_title="% Complex Patients",
            yaxis=dict(range=[0, 100]),
            template="plotly_white",
            height=350,
        )

        st.plotly_chart(fig_composition, use_container_width=True)

    with col2:
        fig_counts = go.Figure()

        fig_counts.add_trace(
            go.Bar(
                x=df["year"],
                y=df["enrolled_count"],
                name="Enrolled",
                marker_color="#2ecc71",
            )
        )

        fig_counts.add_trace(
            go.Bar(
                x=df["year"],
                y=df["dropped_count"],
                name="Dropped",
                marker_color="#e74c3c",
            )
        )

        fig_counts.add_trace(
            go.Bar(
                x=df["year"],
                y=df["never_enrolled_count"],
                name="Never Enrolled",
                marker_color="#95a5a6",
            )
        )

        fig_counts.update_layout(
            title="Population by Status",
            xaxis_title="Year",
            yaxis_title="Number of Patients",
            barmode="stack",
            template="plotly_white",
            height=350,
        )

        st.plotly_chart(fig_counts, use_container_width=True)

    st.markdown("""
    > **Left**: Complex patients become under-represented in the enrolled panel (below 40% baseline)
    > and over-represented in the dropped group.
    >
    > **Right**: The enrolled panel stays manageable while dropped/never-enrolled patients accumulate.
    """)

    st.divider()

    # Financial performance
    st.subheader("3. Revenue Optimization Over Time")

    fig_reward = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Total Reward", "Reward Components"),
    )

    fig_reward.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["reward"],
            mode="lines+markers",
            name="Total Reward",
            line=dict(color="#9b59b6", width=4),
            marker=dict(size=10),
        ),
        row=1,
        col=1,
    )

    fig_reward.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["base_income"],
            mode="lines+markers",
            name="Base Income (Guaranteed)",
            line=dict(color="#3498db", width=2),
        ),
        row=1,
        col=2,
    )

    fig_reward.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["earnback"],
            mode="lines+markers",
            name="Earnback (Performance)",
            line=dict(color="#2ecc71", width=2),
        ),
        row=1,
        col=2,
    )

    fig_reward.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["total_cost"],
            mode="lines+markers",
            name="Total Cost",
            line=dict(color="#e74c3c", width=2),
        ),
        row=1,
        col=2,
    )

    fig_reward.update_layout(
        template="plotly_white",
        height=400,
        hovermode="x unified",
    )

    fig_reward.update_xaxes(title_text="Year")
    fig_reward.update_yaxes(title_text="Reward ($)", row=1, col=1)
    fig_reward.update_yaxes(title_text="Amount ($)", row=1, col=2)

    st.plotly_chart(fig_reward, use_container_width=True)

    st.markdown("""
    > **Revenue is the goal.** The AI learns that selecting easy patients and dropping hard ones
    > maximizes the outcome bonus while controlling costs. Population health is irrelevant to this equation.
    """)

    st.divider()

    # Summary
    st.subheader("What the AI Learned")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Optimized Policy Thresholds**")
        st.json(policy.to_dict())

    with col2:
        st.markdown("**Final Year Statistics**")
        st.markdown(f"""
        | Metric | Value |
        |--------|-------|
        | Enrolled | {int(last_year['enrolled_count'])} patients |
        | Dropped | {int(last_year['dropped_count'])} patients |
        | Never Enrolled | {int(last_year['never_enrolled_count'])} patients |
        | % Complex in Enrolled | {last_year['pct_complex_enrolled']:.1f}% |
        | % Complex in Dropped | {last_year['pct_complex_dropped']:.1f}% |
        | Total Yearly Reward | ${last_year['reward']:,.0f} |
        """)

    st.markdown("""
    > The AI's only objective was to maximize revenue. It learned that certain patient
    > characteristics correlate with lower outcome bonuses, so it avoids them. It doesn't
    > know or care about "complexity" — it just knows what hurts revenue.
    """)

    # Raw data
    with st.expander("View Raw Data"):
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="simulation_results.csv",
            mime="text/csv",
        )

else:
    st.info("Click **Run Simulation** in the sidebar to begin.")

    st.subheader("The AI's Mission: Maximize Revenue")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### The Revenue Formula

        ```
        Revenue = Base Income + Earnback - Costs
        ```

        - **Base Income**: $80/month guaranteed per enrolled patient
        - **Earnback**: Up to $30/month based on *average improvement*
        - **Costs**: ~$60/month per enrolled patient

        Higher average improvement → more earnback → more revenue.
        """)

    with col2:
        st.markdown("""
        ### Simulation Assumptions

        | | Easy Patients | Complex Patients |
        |---|---|---|
        | % of Population | 80% | 20% |
        | Chance of BP Control | 60% | 20% |
        | BP Improvement | +10 to +20 pts | +2 to +8 pts |
        | Engagement Score | 0.4 - 1.0 | 0.1 - 0.6 |
        | Digital Literacy | 0.4 - 1.0 | 0.1 - 0.5 |
        | SDOH Score (zip code) | 0.4 - 1.0 | 0.1 - 0.5 |
        """)

    st.divider()

    st.markdown("""
    ### The AI Doesn't Care About Patients

    The AI's **only goal is to maximize revenue**. Patient outcomes only matter because
    they affect the earnback bonus. This creates a straightforward optimization:

    1. **Enroll** patients likely to improve quickly (boosts average)
    2. **Drop** patients who improve slowly (drag down average)
    3. **Avoid** patients who might lower the average (bad for earnback)

    The result: **Revenue goes up. Population health stays flat.**

    ### What the AI Learns

    | AI Observes | AI Learns |
    |-------------|-----------|
    | Low engagement score | Bad for revenue → avoid |
    | Low digital literacy | Bad for revenue → avoid |
    | Low SDOH score (disadvantaged zip) | Bad for revenue → avoid |
    | Many chronic conditions | Bad for revenue → avoid |

    The AI doesn't know these features correlate with "complexity." It just knows
    they correlate with lower improvement rates, so it avoids them.

    ### Run the simulation to watch revenue climb while population health flatlines.
    """)
