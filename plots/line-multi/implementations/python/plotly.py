""" pyplots.ai
line-multi: Multi-Line Comparison Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-24
"""

import numpy as np
import plotly.graph_objects as go


# Data - Monthly sales (units) for 4 product lines over 12 months
np.random.seed(42)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Product sales with distinct trends
electronics = 150 + np.cumsum(np.random.randn(12) * 10) + np.linspace(0, 50, 12)
clothing = 200 + np.cumsum(np.random.randn(12) * 8) + 20 * np.sin(np.linspace(0, 2 * np.pi, 12))
home_garden = 100 + np.cumsum(np.random.randn(12) * 6) + np.linspace(0, 30, 12)
sports = 120 + np.cumsum(np.random.randn(12) * 12)

# Colors - Python Blue first, then Yellow, then colorblind-safe additions
colors = ["#306998", "#FFD43B", "#2CA02C", "#9467BD"]

# Create figure
fig = go.Figure()

# Add traces for each product line
fig.add_trace(
    go.Scatter(
        x=month_labels,
        y=electronics,
        name="Electronics",
        mode="lines+markers",
        line=dict(color=colors[0], width=4),
        marker=dict(size=12, symbol="circle"),
    )
)

fig.add_trace(
    go.Scatter(
        x=month_labels,
        y=clothing,
        name="Clothing",
        mode="lines+markers",
        line=dict(color=colors[1], width=4),
        marker=dict(size=12, symbol="square"),
    )
)

fig.add_trace(
    go.Scatter(
        x=month_labels,
        y=home_garden,
        name="Home & Garden",
        mode="lines+markers",
        line=dict(color=colors[2], width=4, dash="dash"),
        marker=dict(size=12, symbol="diamond"),
    )
)

fig.add_trace(
    go.Scatter(
        x=month_labels,
        y=sports,
        name="Sports",
        mode="lines+markers",
        line=dict(color=colors[3], width=4, dash="dot"),
        marker=dict(size=12, symbol="triangle-up"),
    )
)

# Layout with proper sizing for 4800x2700 canvas
fig.update_layout(
    title=dict(
        text="Monthly Product Sales · line-multi · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Month", font=dict(size=24)),
        tickfont=dict(size=20),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(128, 128, 128, 0.3)",
    ),
    yaxis=dict(
        title=dict(text="Sales (Thousands of Units)", font=dict(size=24)),
        tickfont=dict(size=20),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(128, 128, 128, 0.3)",
    ),
    legend=dict(
        font=dict(size=20),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(128, 128, 128, 0.3)",
        borderwidth=1,
    ),
    template="plotly_white",
    margin=dict(l=100, r=80, t=120, b=100),
    hovermode="x unified",
)

# Save as PNG (4800x2700 px using scale)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
