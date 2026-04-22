""" pyplots.ai
line-confidence: Line Plot with Confidence Interval
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go


# Data - Monthly temperature forecast with 95% confidence interval
np.random.seed(42)

# Generate 50 months of data
months = np.arange(1, 51)

# Create a realistic temperature trend with seasonality
base_trend = 15 + 0.05 * months  # Slight warming trend
seasonality = 8 * np.sin(2 * np.pi * months / 12)  # Annual cycle
noise = np.random.normal(0, 1.5, len(months))

# Central temperature values (mean forecast)
temperature_mean = base_trend + seasonality + noise

# Confidence interval widens slightly over time (uncertainty grows)
uncertainty = 1.5 + 0.03 * months
y_lower = temperature_mean - 1.96 * uncertainty
y_upper = temperature_mean + 1.96 * uncertainty

# Create figure
fig = go.Figure()

# Add confidence band (shaded area)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([months, months[::-1]]),
        y=np.concatenate([y_upper, y_lower[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.25)",
        line=dict(color="rgba(255, 255, 255, 0)"),
        hoverinfo="skip",
        showlegend=True,
        name="95% Confidence Interval",
    )
)

# Add central line (mean)
fig.add_trace(
    go.Scatter(x=months, y=temperature_mean, mode="lines", line=dict(color="#306998", width=4), name="Mean Temperature")
)

# Update layout for large canvas
fig.update_layout(
    title=dict(text="line-confidence · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Month", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(128, 128, 128, 0.3)",
        gridwidth=1,
        showgrid=True,
    ),
    yaxis=dict(
        title=dict(text="Temperature (°C)", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(128, 128, 128, 0.3)",
        gridwidth=1,
        showgrid=True,
    ),
    legend=dict(
        font=dict(size=18),
        x=0.02,
        y=0.98,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(128, 128, 128, 0.3)",
        borderwidth=1,
    ),
    template="plotly_white",
    margin=dict(l=100, r=60, t=100, b=80),
    plot_bgcolor="white",
)

# Save as PNG (4800 × 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
