""" anyplot.ai
polar-basic: Basic Polar Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-04-30
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.12)" if THEME == "light" else "rgba(240,239,232,0.12)"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Hourly temperature readings over 24 hours (cyclical pattern)
np.random.seed(42)
hours = np.arange(0, 24)
theta = hours * 15  # 360/24 = 15 degrees per hour

# Temperature pattern: cooler at night, warmer during day
base_temp = 15 + 10 * np.sin(np.radians(theta - 90))  # Peak at noon (hour 12)
noise = np.random.randn(24) * 1.5
radius = base_temp + noise

hour_labels = [f"{h:02d}:00" for h in hours]

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatterpolar(
        r=radius,
        theta=theta,
        mode="markers+lines",
        marker={"size": 18, "color": BRAND, "line": {"color": PAGE_BG, "width": 2}},
        line={"width": 3, "color": BRAND},
        fill="toself",
        fillcolor="rgba(0,158,115,0.15)",
        name="Temperature",
        hovertemplate="<b>%{customdata}</b><br>Temperature: %{r:.1f}°C<extra></extra>",
        customdata=hour_labels,
    )
)

fig.update_layout(
    title={"text": "polar-basic · plotly · anyplot.ai", "font": {"size": 28, "color": INK}, "x": 0.5, "xanchor": "center"},
    polar={
        "bgcolor": PAGE_BG,
        "radialaxis": {
            "visible": True,
            "range": [0, max(radius) * 1.1],
            "tickfont": {"size": 18, "color": INK_SOFT},
            "title": {"text": "Temperature (°C)", "font": {"size": 22, "color": INK}},
            "gridcolor": GRID,
            "gridwidth": 1,
            "linecolor": INK_SOFT,
            "linewidth": 1,
        },
        "angularaxis": {
            "tickmode": "array",
            "tickvals": list(range(0, 360, 30)),
            "ticktext": ["0h", "2h", "4h", "6h", "8h", "10h", "12h", "14h", "16h", "18h", "20h", "22h"],
            "tickfont": {"size": 18, "color": INK_SOFT},
            "gridcolor": GRID,
            "gridwidth": 1,
            "direction": "clockwise",
            "rotation": 90,
            "linecolor": INK_SOFT,
            "linewidth": 1,
        },
    },
    paper_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    margin={"l": 80, "r": 80, "t": 120, "b": 80},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
