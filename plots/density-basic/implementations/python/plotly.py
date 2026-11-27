"""anyplot.ai
density-basic: Basic Density Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-30
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome tokens (see default-style-guide.md)
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: first series is always #009E73
BRAND = "#009E73"
FILL = "rgba(0,158,115,0.2)"

# Columns: set this to your table's column name
SAT_MATH = "SAT Math Score (points)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
df = pd.DataFrame({SAT_MATH: np.clip(np.concatenate([rng.normal(540, 60, 350), rng.normal(680, 35, 150)]), 200, 800)})

# Plot
scores = df[SAT_MATH].dropna().to_numpy()
kde = gaussian_kde(scores)
pad = 0.1 * (scores.max() - scores.min())
x_grid = np.linspace(scores.min() - pad, scores.max() + pad, 500)
density = kde(x_grid)

fig = go.Figure()

# KDE curve with filled area
fig.add_trace(
    go.Scatter(
        x=x_grid,
        y=density,
        mode="lines",
        fill="tozeroy",
        fillcolor=FILL,
        line={"color": BRAND, "width": 2.5},
        name="Density",
        hovertemplate="Score: %{x:.0f}<br>Density: %{y:.4f}<extra></extra>",
    )
)

# Rug plot: individual observations as tick marks along the x-axis
fig.add_trace(
    go.Scatter(
        x=scores,
        y=np.zeros(len(scores)),
        mode="markers",
        marker={"symbol": "line-ns", "size": 10, "color": INK_SOFT, "opacity": 0.5, "line": {"width": 1}},
        name="Observations",
        hovertemplate="Score: %{x:.0f}<extra></extra>",
    )
)

fig.update_layout(
    autosize=False,
    title={
        "text": "density-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": SAT_MATH, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "zeroline": False,
        "linecolor": INK_SOFT,
        "showspikes": True,
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": "rgba(0,158,115,0.3)",
        "spikedash": "dot",
    },
    yaxis={
        "title": {"text": "Density", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "rangemode": "tozero",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    hovermode="x",
    margin={"l": 80, "r": 40, "t": 60, "b": 60},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn", config={"displayModeBar": True, "scrollZoom": True})
