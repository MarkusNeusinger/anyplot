""" anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-12
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

# Okabe-Ito palette (first series is ALWAYS #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Product performance across regions
np.random.seed(42)
n_per_group = 40

regions = ["North", "South", "West", "East"]

data = {
    "North": {"x": np.random.normal(35, 8, n_per_group), "y": np.random.normal(75, 10, n_per_group)},
    "South": {"x": np.random.normal(55, 10, n_per_group), "y": np.random.normal(60, 12, n_per_group)},
    "West": {"x": np.random.normal(70, 7, n_per_group), "y": np.random.normal(85, 8, n_per_group)},
    "East": {"x": np.random.normal(45, 9, n_per_group), "y": np.random.normal(45, 10, n_per_group)},
}

# Plot
fig = go.Figure()

for i, region in enumerate(regions):
    fig.add_trace(
        go.Scatter(
            x=data[region]["x"],
            y=data[region]["y"],
            mode="markers",
            name=region,
            marker={"size": 14, "color": IMPRINT[i], "opacity": 0.7, "line": {"width": 1, "color": PAGE_BG}},
            hovertemplate=f"{region}<br>Marketing: %{{x:.1f}}%<br>Sales: %{{y:.1f}}%<extra></extra>",
        )
    )

# Layout
fig.update_layout(
    title={
        "text": "scatter-categorical · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Marketing Investment (%)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "showgrid": True,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Sales Growth (%)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "showgrid": True,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    legend={
        "title": {"text": "Region", "font": {"size": 20, "color": INK}},
        "font": {"size": 18, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 1.02,
        "y": 0.5,
        "yanchor": "middle",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 80, "r": 150, "t": 80, "b": 80},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
