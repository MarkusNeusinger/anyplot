"""anyplot.ai
line-confidence: Line Plot with Confidence Interval
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
TEMPERATURE = "Temperature (°C)"  # role: y
LOWER = "Lower bound (°C)"  # role: y_lower
UPPER = "Upper bound (°C)"  # role: y_upper

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
# Monthly temperature forecast with a 95% confidence interval
rng = np.random.default_rng(42)
months = np.arange(1, 51)
trend = 15 + 0.05 * months  # slight warming trend
seasonality = 8 * np.sin(2 * np.pi * months / 12)  # annual cycle
mean = trend + seasonality + rng.normal(0, 1.5, len(months))
half_width = 1.96 * (1.5 + 0.03 * months)  # uncertainty grows over time
df = pd.DataFrame({MONTH: months, TEMPERATURE: mean, LOWER: mean - half_width, UPPER: mean + half_width})

# Plot: reads only df and the constants above
color = IMPRINT_PALETTE[0]
band_color = f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.25)"

fig = go.Figure()

# Confidence band: invisible upper edge, lower edge fills up to it
fig.add_trace(
    go.Scatter(
        x=df[MONTH],
        y=df[UPPER],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hovertemplate="Upper: %{y:.1f}°C<extra></extra>",
    )
)
fig.add_trace(
    go.Scatter(
        x=df[MONTH],
        y=df[LOWER],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor=band_color,
        name="95% confidence interval",
        hovertemplate="Lower: %{y:.1f}°C<extra></extra>",
    )
)

# Central line drawn last, on top of the band
fig.add_trace(
    go.Scatter(
        x=df[MONTH],
        y=df[TEMPERATURE],
        mode="lines",
        line=dict(color=color, width=2.5),
        name="Mean temperature",
        hovertemplate="Month %{x:.0f}<br>%{y:.1f}°C<extra></extra>",
    )
)

# Style: headroom above the band keeps the legend off the data
span = df[UPPER].max() - df[LOWER].min()
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin=dict(l=80, r=40, t=80, b=60),
    title=dict(text="line-confidence · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5),
    xaxis=dict(
        title=dict(text=MONTH, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        range=[df[LOWER].min() - 0.05 * span, df[UPPER].max() + 0.3 * span],
        title=dict(text=TEMPERATURE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    legend=dict(
        font=dict(size=10, color=INK_SOFT),
        x=0.99,
        y=0.99,
        xanchor="right",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    template="plotly_white",
    font=dict(color=INK),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
