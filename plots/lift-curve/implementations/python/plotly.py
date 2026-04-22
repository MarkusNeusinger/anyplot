""" pyplots.ai
lift-curve: Model Lift Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-27
"""

import numpy as np
import plotly.graph_objects as go


# Data: Simulate customer response model predictions
np.random.seed(42)
n_samples = 1000

# Create realistic model predictions with varying quality
# Higher scores should correlate with positive responses
base_score = np.random.beta(2, 5, n_samples)  # Skewed towards lower scores
true_signal = np.random.rand(n_samples)

# Model scores with some predictive power
y_score = 0.6 * base_score + 0.4 * true_signal
y_score = np.clip(y_score, 0, 1)

# Generate true labels based on scores (with noise for realism)
response_prob = 0.3 * y_score + 0.1  # Base response rate ~10%, up to ~40% for high scores
y_true = (np.random.rand(n_samples) < response_prob).astype(int)

# Calculate lift curve
sorted_indices = np.argsort(y_score)[::-1]  # Sort by score descending
y_true_sorted = y_true[sorted_indices]

# Cumulative response rate at each percentile
cumsum_responses = np.cumsum(y_true_sorted)
total_responses = y_true_sorted.sum()
baseline_rate = total_responses / n_samples

# Calculate lift at each point
percentile = np.arange(1, n_samples + 1) / n_samples * 100
expected_random = np.arange(1, n_samples + 1) * baseline_rate
lift = cumsum_responses / expected_random

# Sample at key percentiles for cleaner visualization
sample_points = [0] + list(range(9, n_samples, 10)) + [n_samples - 1]
percentile_sampled = percentile[sample_points]
lift_sampled = lift[sample_points]

# Create figure
fig = go.Figure()

# Lift curve
fig.add_trace(
    go.Scatter(
        x=percentile_sampled,
        y=lift_sampled,
        mode="lines+markers",
        name="Model Lift",
        line=dict(color="#306998", width=4),
        marker=dict(size=10, color="#306998"),
        hovertemplate="Top %{x:.0f}%<br>Lift: %{y:.2f}x<extra></extra>",
    )
)

# Random selection baseline (lift = 1)
fig.add_trace(
    go.Scatter(
        x=[0, 100],
        y=[1, 1],
        mode="lines",
        name="Random Selection",
        line=dict(color="#FFD43B", width=3, dash="dash"),
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
    arrowcolor="#306998",
    ax=60,
    ay=-40,
    font=dict(size=18, color="#306998"),
    bgcolor="white",
    bordercolor="#306998",
    borderwidth=1,
    borderpad=6,
)

# Layout
fig.update_layout(
    title=dict(text="lift-curve · plotly · pyplots.ai", font=dict(size=32, color="#333333"), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Percentage of Population Targeted (%)", font=dict(size=24)),
        tickfont=dict(size=18),
        range=[0, 100],
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        dtick=10,
    ),
    yaxis=dict(
        title=dict(text="Cumulative Lift Ratio", font=dict(size=24)),
        tickfont=dict(size=18),
        range=[0, max(lift_sampled) * 1.1],
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    template="plotly_white",
    legend=dict(
        font=dict(size=18),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="rgba(0,0,0,0.1)",
        borderwidth=1,
    ),
    margin=dict(l=100, r=80, t=100, b=100),
    plot_bgcolor="white",
    paper_bgcolor="white",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
