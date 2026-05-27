""" anyplot.ai
lift-curve: Model Lift Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-10
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
BRAND = "#009E73"  # First series, always
ACCENT = "#C475FD"  # Second series

# Data: Simulate customer response model predictions
np.random.seed(42)
n_samples = 1000

# Create realistic model predictions with varying quality
base_score = np.random.beta(2, 5, n_samples)
true_signal = np.random.rand(n_samples)

# Model scores with predictive power
y_score = 0.6 * base_score + 0.4 * true_signal
y_score = np.clip(y_score, 0, 1)

# Generate true labels based on scores
response_prob = 0.3 * y_score + 0.1
y_true = (np.random.rand(n_samples) < response_prob).astype(int)

# Calculate lift curve
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

cumsum_responses = np.cumsum(y_true_sorted)
total_responses = y_true_sorted.sum()
baseline_rate = total_responses / n_samples

percentile = np.arange(1, n_samples + 1) / n_samples * 100
expected_random = np.arange(1, n_samples + 1) * baseline_rate
lift = cumsum_responses / expected_random

# Sample at key percentiles for visualization
sample_points = [0] + list(range(9, n_samples, 10)) + [n_samples - 1]
percentile_sampled = percentile[sample_points]
lift_sampled = lift[sample_points]

# Create figure
fig = go.Figure()

# Lift curve (first series = brand color)
fig.add_trace(
    go.Scatter(
        x=percentile_sampled,
        y=lift_sampled,
        mode="lines+markers",
        name="Model Lift",
        line=dict(color=BRAND, width=4),
        marker=dict(size=10, color=BRAND),
        hovertemplate="Top %{x:.0f}%<br>Lift: %{y:.2f}x<extra></extra>",
    )
)

# Random selection baseline (second series = accent color)
fig.add_trace(
    go.Scatter(
        x=[0, 100],
        y=[1, 1],
        mode="lines",
        name="Random Selection",
        line=dict(color=ACCENT, width=3, dash="dash"),
        hovertemplate="Random baseline<br>Lift: 1.0x<extra></extra>",
    )
)

# Add annotation for key insight
top_10_lift = lift[int(n_samples * 0.1) - 1]
fig.add_annotation(
    x=10,
    y=top_10_lift,
    text=f"Top 10%: {top_10_lift:.1f}x lift",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2,
    arrowcolor=BRAND,
    ax=60,
    ay=-40,
    font=dict(size=18, color=INK),
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=6,
)

# Layout with theme-adaptive colors
fig.update_layout(
    title=dict(text="lift-curve · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Percentage of Population Targeted (%)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        range=[0, 100],
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        dtick=10,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Cumulative Lift Ratio", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        range=[0, max(lift_sampled) * 1.1],
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend=dict(
        font=dict(size=16, color=INK_SOFT),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=100, r=80, t=100, b=100),
)

# Save with theme suffix
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
