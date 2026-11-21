"""anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SMOOTHING_FRAC = 0.35  # LOWESS bandwidth: share of points in each local fit (spec: 0.3-0.5)

# Columns: set these to your table's column names
SUBSTRATE = "Substrate Concentration (µM)"  # role: x
ACTIVITY = "Enzyme Activity (V/V_max)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
# Enzyme kinetics: Michaelis-Menten saturation with measurement noise and a slow ripple
np.random.seed(42)
substrate = np.linspace(0.1, 50, 150)
activity = (100 * substrate) / (10 + substrate) + np.random.normal(0, 3, substrate.size) + 5 * np.sin(substrate / 5)
df = pd.DataFrame({SUBSTRATE: substrate, ACTIVITY: activity})

# Plot: reads only df and the constants above
valid = df.dropna(subset=[SUBSTRATE, ACTIVITY])
smoothed = lowess(valid[ACTIVITY], valid[SUBSTRATE], frac=SMOOTHING_FRAC, it=3)

title = "scatter-regression-lowess · python · plotly · anyplot.ai"

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[SUBSTRATE],
        y=df[ACTIVITY],
        mode="markers",
        name="Measured values",
        marker={"size": 7, "color": IMPRINT_PALETTE[0], "opacity": 0.6, "line": {"color": PAGE_BG, "width": 0.5}},
    )
)
fig.add_trace(
    go.Scatter(
        x=smoothed[:, 0],
        y=smoothed[:, 1],
        mode="lines",
        name="LOWESS smooth",
        line={"color": IMPRINT_PALETTE[1], "width": 3},
    )
)

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 80, "r": 40, "t": 70, "b": 65},
    title={"text": title, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": SUBSTRATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": ACTIVITY, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    showlegend=True,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
