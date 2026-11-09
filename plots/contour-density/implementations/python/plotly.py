"""anyplot.ai
contour-density: Density Contour Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
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
POINT_INK = "rgba(26,26,23,0.30)" if THEME == "light" else "rgba(240,239,232,0.30)"

# Imprint sequential colormap (brand green → blue); the lowest band fades into the page
# so empty space stays background and the strongest blue marks the highest density
BRAND = "#009E73"
IMPRINT_SEQ = [[0.0, "rgba(0,158,115,0)"], [0.08, BRAND], [1.0, "#4467A3"]]

# Columns: set these to your table's column names
HEIGHT = "Height (cm)"  # role: x
WEIGHT = "Weight (kg)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
np.random.seed(42)
n_points = 500
cluster1_x = np.random.normal(160, 8, n_points // 3)  # lighter individuals
cluster1_y = np.random.normal(60, 6, n_points // 3)
cluster2_x = np.random.normal(175, 10, n_points // 3)  # heavier individuals
cluster2_y = np.random.normal(80, 8, n_points // 3)
cluster3_x = np.random.normal(180, 7, n_points // 3)  # tall but lighter individuals
cluster3_y = np.random.normal(70, 7, n_points // 3)
df = pd.DataFrame(
    {
        HEIGHT: np.concatenate([cluster1_x, cluster2_x, cluster3_x]),
        WEIGHT: np.concatenate([cluster1_y, cluster2_y, cluster3_y]),
    }
)

# Plot: reads only df and the constants above
points = df[[HEIGHT, WEIGHT]].dropna()
hover = f"{HEIGHT}: %{{x:.1f}}<br>{WEIGHT}: %{{y:.1f}}"

fig = go.Figure()

fig.add_trace(
    go.Histogram2dContour(
        x=points[HEIGHT],
        y=points[WEIGHT],
        colorscale=IMPRINT_SEQ,
        contours={"showlabels": False, "coloring": "fill"},
        ncontours=14,
        showscale=True,
        colorbar={
            "title": {"text": "Density", "font": {"size": 12, "color": INK}},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "len": 0.8,
            "thickness": 16,
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
            "outlinewidth": 0,
        },
        line={"width": 1, "color": PAGE_BG},
        hovertemplate=f"<b>Density region</b><br>{hover}<extra></extra>",
    )
)

# Faint scatter overlay at the exact values, so the contours stay the main signal
fig.add_trace(
    go.Scatter(
        x=points[HEIGHT],
        y=points[WEIGHT],
        mode="markers",
        marker={"size": 4, "color": POINT_INK, "line": {"width": 0}},
        showlegend=False,
        name="Individual measurements",
        hovertemplate=f"<b>Measurement</b><br>{hover}<extra></extra>",
    )
)

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    title={
        "text": "contour-density · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": HEIGHT, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": WEIGHT, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    hovermode="closest",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
