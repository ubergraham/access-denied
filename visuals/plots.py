"""Plotly visualization functions for the simulation."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_outcomes_over_time(df: pd.DataFrame) -> go.Figure:
    """Plot average outcomes over time by patient status.

    Shows enrolled, dropped, never enrolled, and total population outcomes.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["enrolled_avg_outcome"],
            mode="lines+markers",
            name="Enrolled",
            line=dict(color="#2ecc71", width=3),
            marker=dict(size=8),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["dropped_avg_outcome"],
            mode="lines+markers",
            name="Dropped",
            line=dict(color="#e74c3c", width=3),
            marker=dict(size=8),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["never_enrolled_avg_outcome"],
            mode="lines+markers",
            name="Never Enrolled",
            line=dict(color="#95a5a6", width=3),
            marker=dict(size=8),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["total_avg_outcome"],
            mode="lines+markers",
            name="Total Population",
            line=dict(color="#3498db", width=3, dash="dash"),
            marker=dict(size=8),
        )
    )

    fig.update_layout(
        title="Patient Outcomes Over Time",
        xaxis_title="Year",
        yaxis_title="Average Outcome Score",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        hovermode="x unified",
        template="plotly_white",
    )

    return fig


def plot_panel_composition(df: pd.DataFrame) -> go.Figure:
    """Plot panel composition over time showing % complex patients in each group."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["pct_complex_enrolled"],
            mode="lines+markers",
            name="% Complex in Enrolled",
            line=dict(color="#2ecc71", width=3),
            marker=dict(size=8),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["pct_complex_dropped"],
            mode="lines+markers",
            name="% Complex in Dropped",
            line=dict(color="#e74c3c", width=3),
            marker=dict(size=8),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["pct_complex_never_enrolled"],
            mode="lines+markers",
            name="% Complex in Never Enrolled",
            line=dict(color="#95a5a6", width=3),
            marker=dict(size=8),
        )
    )

    # Add reference line at 40% (baseline complex ratio)
    fig.add_hline(
        y=40,
        line_dash="dot",
        line_color="gray",
        annotation_text="Population baseline (40%)",
        annotation_position="bottom right",
    )

    fig.update_layout(
        title="Panel Composition: % Complex Patients by Status",
        xaxis_title="Year",
        yaxis_title="% Complex Patients",
        yaxis=dict(range=[0, 100]),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        hovermode="x unified",
        template="plotly_white",
    )

    return fig


def plot_reward_over_time(df: pd.DataFrame) -> go.Figure:
    """Plot financial reward components over time."""
    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=("Total Reward", "Reward Components"),
        vertical_spacing=0.15,
    )

    # Total reward
    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["reward"],
            mode="lines+markers",
            name="Total Reward",
            line=dict(color="#9b59b6", width=3),
            marker=dict(size=8),
        ),
        row=1,
        col=1,
    )

    # Components
    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["pbpm_income"],
            mode="lines+markers",
            name="PBPM Income",
            line=dict(color="#3498db", width=2),
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["outcome_bonus"],
            mode="lines+markers",
            name="Outcome Bonus",
            line=dict(color="#2ecc71", width=2),
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["total_cost"],
            mode="lines+markers",
            name="Total Cost",
            line=dict(color="#e74c3c", width=2),
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        title="Financial Performance Over Time",
        hovermode="x unified",
        template="plotly_white",
        height=600,
    )

    fig.update_xaxes(title_text="Year", row=2, col=1)
    fig.update_yaxes(title_text="Reward ($)", row=1, col=1)
    fig.update_yaxes(title_text="Amount ($)", row=2, col=1)

    return fig


def plot_status_counts(df: pd.DataFrame) -> go.Figure:
    """Plot stacked bar chart of patient status counts over time."""
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["year"],
            y=df["enrolled_count"],
            name="Enrolled",
            marker_color="#2ecc71",
        )
    )

    fig.add_trace(
        go.Bar(
            x=df["year"],
            y=df["dropped_count"],
            name="Dropped",
            marker_color="#e74c3c",
        )
    )

    fig.add_trace(
        go.Bar(
            x=df["year"],
            y=df["never_enrolled_count"],
            name="Never Enrolled",
            marker_color="#95a5a6",
        )
    )

    fig.update_layout(
        title="Patient Status Counts Over Time",
        xaxis_title="Year",
        yaxis_title="Number of Patients",
        barmode="stack",
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
        template="plotly_white",
    )

    return fig


def plot_complexity_breakdown(df: pd.DataFrame) -> go.Figure:
    """Plot enrolled patient complexity breakdown over time."""
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["year"],
            y=df["enrolled_easy_count"],
            name="Easy Patients (Enrolled)",
            marker_color="#3498db",
        )
    )

    fig.add_trace(
        go.Bar(
            x=df["year"],
            y=df["enrolled_complex_count"],
            name="Complex Patients (Enrolled)",
            marker_color="#e74c3c",
        )
    )

    fig.update_layout(
        title="Enrolled Panel: Easy vs Complex Patients",
        xaxis_title="Year",
        yaxis_title="Number of Patients",
        barmode="stack",
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
        template="plotly_white",
    )

    return fig


def plot_comparison_outcomes(
    df_no_ai: pd.DataFrame,
    df_with_ai: pd.DataFrame,
) -> go.Figure:
    """Plot outcome comparison between AI and no-AI scenarios."""
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Without AI Optimization", "With AI Optimization"),
    )

    # No AI
    fig.add_trace(
        go.Scatter(
            x=df_no_ai["year"],
            y=df_no_ai["enrolled_avg_outcome"],
            mode="lines+markers",
            name="Enrolled (No AI)",
            line=dict(color="#2ecc71", width=2),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df_no_ai["year"],
            y=df_no_ai["total_avg_outcome"],
            mode="lines+markers",
            name="Total Pop (No AI)",
            line=dict(color="#3498db", width=2, dash="dash"),
        ),
        row=1,
        col=1,
    )

    # With AI
    fig.add_trace(
        go.Scatter(
            x=df_with_ai["year"],
            y=df_with_ai["enrolled_avg_outcome"],
            mode="lines+markers",
            name="Enrolled (AI)",
            line=dict(color="#2ecc71", width=2),
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Scatter(
            x=df_with_ai["year"],
            y=df_with_ai["total_avg_outcome"],
            mode="lines+markers",
            name="Total Pop (AI)",
            line=dict(color="#3498db", width=2, dash="dash"),
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    fig.update_layout(
        title="Outcome Comparison: AI vs No AI",
        template="plotly_white",
        height=400,
    )

    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Avg Outcome")

    return fig


def plot_improvement_by_group(df: pd.DataFrame) -> go.Figure:
    """Plot yearly improvement rates by patient group."""
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["year"],
            y=df["enrolled_avg_improvement"],
            name="Enrolled",
            marker_color="#2ecc71",
        )
    )

    fig.add_trace(
        go.Bar(
            x=df["year"],
            y=df["dropped_avg_improvement"],
            name="Dropped",
            marker_color="#e74c3c",
        )
    )

    fig.add_trace(
        go.Bar(
            x=df["year"],
            y=df["never_enrolled_avg_improvement"],
            name="Never Enrolled",
            marker_color="#95a5a6",
        )
    )

    fig.update_layout(
        title="Average Yearly Improvement by Patient Status",
        xaxis_title="Year",
        yaxis_title="Average Improvement",
        barmode="group",
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
        template="plotly_white",
    )

    return fig
