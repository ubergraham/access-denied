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


st.set_page_config(
    page_title="ACCESS Incentive Simulator",
    page_icon="🏥",
    layout="wide",
)

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

if st.sidebar.button("Single Organization", type="primary", use_container_width=True):
    with st.spinner("AI is learning to maximize revenue..."):
        df, policy, _ = run_simulation(config, enable_ai_optimization=True)
        st.session_state["df"] = df
        st.session_state["policy"] = policy
        st.session_state["mode"] = "single"
    st.rerun()

if st.sidebar.button("🍒 Cherry vs 🍇 Grape", use_container_width=True):
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

    # Stroke events chart
    st.markdown("### Adverse Events: Strokes from Uncontrolled Blood Pressure")

    st.markdown("""
    Patients with poorly controlled blood pressure face real health consequences.
    **1% of patients with uncontrolled BP have a stroke each year.**
    """)

    fig_strokes = go.Figure()

    # Cherry strokes by group
    fig_strokes.add_trace(
        go.Scatter(
            x=cherry_df["year"],
            y=cherry_df["strokes_enrolled"],
            mode="lines+markers",
            name="🍒 Cherry (Enrolled)",
            line=dict(color="#e74c3c", width=3),
            marker=dict(size=8),
        )
    )

    fig_strokes.add_trace(
        go.Scatter(
            x=cherry_df["year"],
            y=cherry_df["strokes_dropped"] + cherry_df["strokes_never_enrolled"],
            mode="lines+markers",
            name="🍒 Cherry (Dropped + Rejected)",
            line=dict(color="#e74c3c", width=2, dash="dash"),
            marker=dict(size=5),
        )
    )

    # Grape strokes by group
    fig_strokes.add_trace(
        go.Scatter(
            x=grape_df["year"],
            y=grape_df["strokes_enrolled"],
            mode="lines+markers",
            name="🍇 Grape (Enrolled)",
            line=dict(color="#9b59b6", width=3),
            marker=dict(size=8),
        )
    )

    fig_strokes.add_trace(
        go.Scatter(
            x=grape_df["year"],
            y=grape_df["strokes_dropped"] + grape_df["strokes_never_enrolled"],
            mode="lines+markers",
            name="🍇 Grape (Dropped + Rejected)",
            line=dict(color="#9b59b6", width=2, dash="dash"),
            marker=dict(size=5),
        )
    )

    fig_strokes.update_layout(
        xaxis_title="Year",
        yaxis_title="Number of Strokes",
        template="plotly_white",
        height=400,
        legend=dict(font=dict(size=10)),
    )

    st.plotly_chart(fig_strokes, use_container_width=True)

    st.warning("""
    **The strokes among enrolled patients decrease** (solid lines) because the AI selects healthier patients.

    **But strokes among excluded patients persist** (dashed lines) — these are the people who most need help, left behind by the incentive structure.
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

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🍒 Cherry**")
        cherry_flow = []
        for _, row in cherry_df.iterrows():
            cherry_flow.append({
                "Year": int(row["year"]),
                "Enrolled": f"{int(row['enrolled_count']):,}",
                "Dropped": f"{int(row['dropped_count']):,}",
                "Rejected": f"{int(row['never_enrolled_count']):,}",
            })
        st.table(pd.DataFrame(cherry_flow).set_index("Year"))

    with col2:
        st.markdown("**🍇 Grape**")
        grape_flow = []
        for _, row in grape_df.iterrows():
            grape_flow.append({
                "Year": int(row["year"]),
                "Enrolled": f"{int(row['enrolled_count']):,}",
                "Dropped": f"{int(row['dropped_count']):,}",
                "Rejected": f"{int(row['never_enrolled_count']):,}",
            })
        st.table(pd.DataFrame(grape_flow).set_index("Year"))

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
