""" anyplot.ai
line-stepwise: Step Line Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-13
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
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Server response time monitoring (discrete state changes)
np.random.seed(42)
hours = np.arange(0, 24, 1)
response_times = np.array(
    [
        45,
        45,
        42,
        42,
        48,
        55,
        65,
        72,
        78,
        82,  # Morning ramp-up
        80,
        75,
        85,
        90,
        88,
        85,
        78,
        65,
        55,
        50,  # Afternoon peak
        48,
        45,
        44,
        43,  # Evening decline
    ]
)

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=hours,
        y=response_times,
        mode="lines+markers",
        line={"shape": "hv", "color": BRAND, "width": 4},
        marker={"size": 14, "color": BRAND, "line": {"color": PAGE_BG, "width": 2}},
        name="Response Time",
        hovertemplate="Hour: %{x}<br>Response: %{y} ms<extra></extra>",
    )
)

# Style
fig.update_layout(
    title={
        "text": "line-stepwise · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Hour of Day", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "tickmode": "linear",
        "tick0": 0,
        "dtick": 2,
        "range": [-0.5, 23.5],
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Response Time (ms)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "range": [35, 95],
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    showlegend=False,
    margin={"l": 100, "r": 80, "t": 120, "b": 100},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
