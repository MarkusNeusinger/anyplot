"""anyplot.ai
line-confidence: Line Plot with Confidence Interval
Library: plotly 6.5.0 | Python 3.13
Quality: 93/100 | Updated: 2025-12-26
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1 — ALWAYS first series

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

# Add confidence band (shaded area) with custom hover
band_color = f"rgba({int(BRAND[1:3], 16)}, {int(BRAND[3:5], 16)}, {int(BRAND[5:7], 16)}, 0.25)"
fig.add_trace(
    go.Scatter(
        x=np.concatenate([months, months[::-1]]),
        y=np.concatenate([y_upper, y_lower[::-1]]),
        fill="toself",
        fillcolor=band_color,
        line=dict(color="rgba(255, 255, 255, 0)"),
        hovertemplate="<b>95% CI</b><br>Month: %{x:.0f}<extra></extra>",
        showlegend=True,
        name="95% Confidence Interval",
    )
)

# Add central line (mean) with custom hover
fig.add_trace(
    go.Scatter(
        x=months,
        y=temperature_mean,
        mode="lines",
        line=dict(color=BRAND, width=4),
        hovertemplate="<b>Mean Temperature</b><br>Month: %{x:.0f}<br>Temp: %{y:.1f}°C<extra></extra>",
        name="Mean Temperature",
    )
)

# Update layout for large canvas with theme-adaptive colors
fig.update_layout(
    title=dict(text="line-confidence · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Month", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        showgrid=True,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Temperature (°C)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        showgrid=True,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    legend=dict(
        font=dict(size=18, color=INK_SOFT),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    template="plotly_white",
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=dict(l=100, r=60, t=100, b=80),
)

# Save as PNG (4800 × 2700 px)
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
