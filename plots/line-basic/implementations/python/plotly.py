"""anyplot.ai
line-basic: Basic Line Plot
Library: plotly | Python 3.13
Quality: pending | Updated: 2026-04-29
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
BRAND = "#009E73"

# Data - Monthly temperature readings (seasonal pattern)
np.random.seed(42)
months = np.arange(1, 13)
temperature = 15 + 12 * np.sin((months - 4) * np.pi / 6) + np.random.randn(12) * 1.5

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=months,
        y=temperature,
        mode="lines+markers",
        line={"color": BRAND, "width": 5},
        marker={"size": 18, "color": BRAND},
        hovertemplate="Month: %{x}<br>Temperature: %{y:.1f}°C<extra></extra>",
    )
)

fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": "line-basic · plotly · anyplot.ai",
        "font": {"size": 36, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Month", "font": {"size": 28, "color": INK}},
        "tickfont": {"size": 22, "color": INK_SOFT},
        "tickmode": "array",
        "tickvals": months,
        "ticktext": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": GRID,
    },
    yaxis={
        "title": {"text": "Temperature (°C)", "font": {"size": 28, "color": INK}},
        "tickfont": {"size": 22, "color": INK_SOFT},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": GRID,
    },
    margin={"t": 120, "b": 100, "l": 120, "r": 60},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
