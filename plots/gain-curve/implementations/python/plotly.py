""" pyplots.ai
gain-curve: Cumulative Gains Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-29
"""

import numpy as np
import plotly.graph_objects as go


# Data - Customer response model evaluation
np.random.seed(42)
n_samples = 1000

# Simulate a classification model with moderate discrimination
# Positive class ~20% of population
positive_rate = 0.20
y_true = np.random.binomial(1, positive_rate, n_samples)

# Generate predicted scores that correlate with true labels
# Good predictions: positives tend to have higher scores
y_score = np.where(
    y_true == 1,
    np.random.beta(5, 2, n_samples),  # Positives: skewed toward higher scores
    np.random.beta(2, 5, n_samples),  # Negatives: skewed toward lower scores
)
# Add some noise to make it realistic
y_score = np.clip(y_score + np.random.normal(0, 0.1, n_samples), 0, 1)

# Calculate cumulative gains
sorted_indices = np.argsort(y_score)[::-1]  # Sort by score descending
y_true_sorted = y_true[sorted_indices]

# Cumulative sum of positives
cumulative_positives = np.cumsum(y_true_sorted)
total_positives = y_true.sum()

# Percentage of population (x-axis)
pct_population = np.arange(1, n_samples + 1) / n_samples * 100

# Percentage of positives captured (y-axis)
pct_positives_captured = cumulative_positives / total_positives * 100

# Add origin point for complete curve
pct_population = np.insert(pct_population, 0, 0)
pct_positives_captured = np.insert(pct_positives_captured, 0, 0)

# Perfect model curve
pct_for_perfect = positive_rate * 100
perfect_x = [0, pct_for_perfect, 100]
perfect_y = [0, 100, 100]

# Plot
fig = go.Figure()

# Random baseline (diagonal)
fig.add_trace(
    go.Scatter(
        x=[0, 100], y=[0, 100], mode="lines", name="Random (Baseline)", line=dict(color="#888888", width=3, dash="dash")
    )
)

# Perfect model
fig.add_trace(
    go.Scatter(
        x=perfect_x, y=perfect_y, mode="lines", name="Perfect Model", line=dict(color="#FFD43B", width=3, dash="dot")
    )
)

# Model gains curve
fig.add_trace(
    go.Scatter(
        x=pct_population,
        y=pct_positives_captured,
        mode="lines",
        name="Model",
        line=dict(color="#306998", width=4),
        fill="tonexty",
        fillcolor="rgba(48, 105, 152, 0.2)",
    )
)

# Layout
fig.update_layout(
    title=dict(text="gain-curve · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Percentage of Population Targeted (%)", font=dict(size=22)),
        tickfont=dict(size=18),
        range=[0, 100],
        dtick=20,
        showgrid=True,
        gridcolor="rgba(0, 0, 0, 0.1)",
    ),
    yaxis=dict(
        title=dict(text="Percentage of Positives Captured (%)", font=dict(size=22)),
        tickfont=dict(size=18),
        range=[0, 100],
        dtick=20,
        showgrid=True,
        gridcolor="rgba(0, 0, 0, 0.1)",
    ),
    template="plotly_white",
    legend=dict(
        x=0.98,
        y=0.02,
        xanchor="right",
        yanchor="bottom",
        font=dict(size=18),
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.2)",
        borderwidth=1,
    ),
    margin=dict(l=80, r=40, t=80, b=80),
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
