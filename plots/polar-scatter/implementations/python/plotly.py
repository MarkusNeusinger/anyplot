""" anyplot.ai
polar-scatter: Polar Scatter Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-09
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

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - synthetic wind measurements with prevailing directions
np.random.seed(42)
n_points = 120

# Create wind data with prevailing directions (NW and SE winds common)
# Cluster 1: Northwest winds (~315°)
n1 = 45
angles1 = np.random.normal(315, 25, n1)
speeds1 = np.random.gamma(3, 3, n1) + 5

# Cluster 2: Southeast winds (~135°)
n2 = 40
angles2 = np.random.normal(135, 30, n2)
speeds2 = np.random.gamma(2.5, 2.5, n2) + 3

# Cluster 3: Scattered winds from other directions
n3 = n_points - n1 - n2
angles3 = np.random.uniform(0, 360, n3)
speeds3 = np.random.gamma(2, 2, n3) + 2

# Combine all data
angles = np.concatenate([angles1, angles2, angles3])
angles = angles % 360  # Normalize to 0-360
speeds = np.concatenate([speeds1, speeds2, speeds3])

# Create time of day categories for color encoding
hours = np.random.choice([6, 9, 12, 15, 18], n_points)
time_labels = np.array(["Morning" if h <= 9 else "Afternoon" if h <= 15 else "Evening" for h in hours])

# Create figure
fig = go.Figure()

# Color mapping for time of day using Okabe-Ito
colors = {"Morning": IMPRINT[0], "Afternoon": IMPRINT[1], "Evening": IMPRINT[2]}

# Add traces for each time period
for period in ["Morning", "Afternoon", "Evening"]:
    mask = time_labels == period
    fig.add_trace(
        go.Scatterpolar(
            r=speeds[mask],
            theta=angles[mask],
            mode="markers",
            name=period,
            marker={"size": 14, "color": colors[period], "opacity": 0.75, "line": {"width": 1, "color": PAGE_BG}},
        )
    )

# Update layout for 4800x2700 px canvas
fig.update_layout(
    title={
        "text": "Wind Observations · polar-scatter · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    font={"size": 18, "color": INK},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    polar={
        "bgcolor": PAGE_BG,
        "angularaxis": {
            "tickmode": "array",
            "tickvals": [0, 45, 90, 135, 180, 225, 270, 315],
            "ticktext": ["N (0°)", "NE", "E (90°)", "SE", "S (180°)", "SW", "W (270°)", "NW"],
            "tickfont": {"size": 18, "color": INK_SOFT},
            "direction": "clockwise",
            "rotation": 90,
            "gridcolor": GRID,
            "linecolor": INK_SOFT,
        },
        "radialaxis": {
            "title": {"text": "Wind Speed (m/s)", "font": {"size": 22, "color": INK}},
            "tickfont": {"size": 16, "color": INK_SOFT},
            "gridcolor": GRID,
            "linecolor": INK_SOFT,
            "range": [0, max(speeds) * 1.1],
        },
    },
    legend={
        "title": {"text": "Time of Day", "font": {"size": 20, "color": INK}},
        "font": {"size": 18, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 1.02,
        "y": 0.98,
        "xanchor": "left",
        "yanchor": "top",
    },
    margin={"l": 80, "r": 180, "t": 100, "b": 80},
)

# Save as PNG and HTML with theme suffix
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
