""" anyplot.ai
ridgeline-basic: Basic Ridgeline Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-04-30
"""

import os

import numpy as np
import plotly.colors
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
LINE_EDGE = "rgba(26,26,23,0.35)" if THEME == "light" else "rgba(240,239,232,0.35)"

# Data - Monthly temperature distributions (Northern hemisphere)
np.random.seed(42)

months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

base_temps = [-2, 0, 5, 12, 18, 23, 26, 25, 20, 13, 6, 1]
data = {}
for i, month in enumerate(months):
    std = 4 if i in [2, 3, 8, 9] else 3
    data[month] = np.random.normal(base_temps[i], std, 200)

# X range for density evaluation
x_range = np.linspace(-15, 40, 300)

# Viridis sequential colormap - 12 evenly spaced samples (CVD-safe, perceptually uniform)
colors = plotly.colors.sample_colorscale("viridis", [i / 11 for i in range(12)])

# Plot
fig = go.Figure()

# Scaling for ridge height and ~50% overlap per spec
ridge_scale = 0.12
overlap = 0.5

# Add ridges bottom-to-top so January sits at the bottom
for i, month in enumerate(reversed(months)):
    idx = len(months) - 1 - i
    temps = data[month]

    kde = gaussian_kde(temps)
    density = kde(x_range)
    density = density / density.max() * ridge_scale
    y_offset = i * (1 - overlap) * ridge_scale
    y_fill = density + y_offset

    fig.add_trace(
        go.Scatter(
            x=np.concatenate([[x_range[0]], x_range, [x_range[-1]]]),
            y=np.concatenate([[y_offset], y_fill, [y_offset]]),
            fill="toself",
            fillcolor=colors[idx],
            line={"color": LINE_EDGE, "width": 1.5},
            mode="lines",
            name=month,
            showlegend=False,
            hovertemplate=f"{month}<br>Temperature: %{{x:.1f}}°C<extra></extra>",
        )
    )

# Y-tick positions aligned to ridge peaks
y_ticks = [(len(months) - 1 - i) * (1 - overlap) * ridge_scale + ridge_scale * 0.4 for i in range(len(months))]

# Style
fig.update_layout(
    title={
        "text": "ridgeline-basic · plotly · anyplot.ai",
        "font": {"size": 48, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Temperature (°C)", "font": {"size": 36, "color": INK}},
        "tickfont": {"size": 28, "color": INK_SOFT},
        "range": [-15, 40],
        "gridcolor": GRID,
        "showgrid": True,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "", "font": {"size": 36}},
        "tickfont": {"size": 28, "color": INK_SOFT},
        "tickvals": y_ticks,
        "ticktext": list(reversed(months)),
        "showgrid": False,
        "zeroline": False,
        "range": [-0.02, max(y_ticks) + ridge_scale * 0.7],
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 180, "r": 60, "t": 120, "b": 160},
    annotations=[
        {
            "x": 0.5,
            "y": -0.08,
            "xref": "paper",
            "yref": "paper",
            "text": "Sequential viridis colormap differentiates all 12 monthly ridges (perceptually uniform, CVD-safe)",
            "showarrow": False,
            "font": {"size": 20, "color": INK_SOFT},
            "align": "center",
        }
    ],
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
