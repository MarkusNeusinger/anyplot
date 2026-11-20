"""anyplot.ai
polar-scatter: Polar Scatter Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DIRECTION = "Wind direction (°)"  # role: theta
SPEED = "Wind speed (m/s)"  # role: radius
PERIOD = "Time of day"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
np.random.seed(42)
n_points = 120

# Prevailing north-westerly winds (~315°)
n1 = 45
angles1 = np.random.normal(315, 25, n1)
speeds1 = np.random.gamma(3, 3, n1) + 5

# Prevailing south-easterly winds (~135°)
n2 = 40
angles2 = np.random.normal(135, 30, n2)
speeds2 = np.random.gamma(2.5, 2.5, n2) + 3

# Scattered winds from other directions
n3 = n_points - n1 - n2
angles3 = np.random.uniform(0, 360, n3)
speeds3 = np.random.gamma(2, 2, n3) + 2

hours = np.random.choice([6, 9, 12, 15, 18], n_points)
df = pd.DataFrame(
    {
        DIRECTION: np.concatenate([angles1, angles2, angles3]) % 360,
        SPEED: np.concatenate([speeds1, speeds2, speeds3]),
        PERIOD: ["Morning" if h <= 9 else "Afternoon" if h <= 15 else "Evening" for h in hours],
    }
)

# Plot
fig = go.Figure()
for i, (period, rows) in enumerate(df.groupby(PERIOD, sort=False)):
    fig.add_trace(
        go.Scatterpolar(
            r=rows[SPEED],
            theta=rows[DIRECTION],
            mode="markers",
            name=str(period),
            marker={"size": 8, "color": IMPRINT_PALETTE[i], "opacity": 0.75, "line": {"width": 0.6, "color": PAGE_BG}},
        )
    )

fig.update_layout(
    autosize=False,
    width=600,
    height=600,
    title={
        "text": "Wind Observations · polar-scatter · python · plotly · anyplot.ai",
        "font": {"size": 15, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    font={"size": 11, "color": INK},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    polar={
        "bgcolor": PAGE_BG,
        "angularaxis": {
            "tickmode": "array",
            "tickvals": [0, 45, 90, 135, 180, 225, 270, 315],
            "ticktext": ["N (0°)", "NE", "E (90°)", "SE", "S (180°)", "SW", "W (270°)", "NW"],
            "tickfont": {"size": 12, "color": INK_SOFT},
            "direction": "clockwise",
            "rotation": 90,
            "gridcolor": GRID,
            "linecolor": INK_SOFT,
        },
        "radialaxis": {
            "title": {"text": SPEED, "font": {"size": 12, "color": INK}},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "gridcolor": GRID,
            "linecolor": INK_SOFT,
            "range": [0, df[SPEED].max() * 1.1],
            "angle": 22.5,
        },
    },
    legend={
        "title": {"text": PERIOD, "font": {"size": 12, "color": INK}},
        "font": {"size": 11, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "orientation": "h",
        "x": 0.5,
        "y": -0.04,
        "xanchor": "center",
        "yanchor": "top",
    },
    margin={"l": 60, "r": 60, "t": 60, "b": 70},
)

fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
