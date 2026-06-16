""" anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
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

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]
wind_speed_labels = ["Light (0-10 km/h)", "Moderate (10-20 km/h)", "Strong (20+ km/h)"]

# Data: Wind speed distribution by direction (8 compass points)
np.random.seed(42)
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Wind speed frequencies by direction (coastal wind pattern)
light = np.array([8, 5, 4, 3, 6, 12, 15, 10])
moderate = np.array([6, 4, 3, 2, 4, 10, 12, 8])
strong = np.array([3, 2, 1, 1, 2, 5, 6, 4])

# Create figure with polar subplot
fig = go.Figure()

# Add stacked bars for each wind speed category
for data, label, color in zip([light, moderate, strong], wind_speed_labels, IMPRINT, strict=True):
    fig.add_trace(
        go.Barpolar(
            r=data,
            theta=directions,
            name=label,
            marker=dict(color=color, line=dict(color=PAGE_BG, width=2)),
            hovertemplate="<b>%{theta}</b><br>%{customdata}<br>Frequency: %{r}<extra></extra>",
            customdata=[label] * len(directions),
            opacity=0.9,
        )
    )

# Update layout for polar chart with theme-adaptive styling
fig.update_layout(
    title=dict(text="polar-bar · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    polar=dict(
        barmode="stack",
        radialaxis=dict(
            visible=True,
            range=[0, max(light + moderate + strong) + 3],
            tickfont=dict(size=18, color=INK_SOFT),
            gridcolor=GRID,
            linecolor=INK_SOFT,
            title=dict(text="Frequency", font=dict(size=20, color=INK)),
        ),
        angularaxis=dict(
            tickfont=dict(size=22, color=INK), direction="clockwise", rotation=90, gridcolor=GRID, linecolor=INK_SOFT
        ),
    ),
    legend=dict(
        font=dict(size=18, color=INK_SOFT), x=0.85, y=0.95, bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, borderwidth=1
    ),
    margin=dict(l=100, r=200, t=120, b=100),
)

# Save as PNG (4800 x 2700 px) and interactive HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
