""" anyplot.ai
histogram-density: Density Histogram
Library: plotly 7.1.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SCORE = "Test Score (points)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
df = pd.DataFrame(
    {
        SCORE: np.concatenate(
            [
                np.random.normal(loc=65, scale=8, size=350),  # main group (lower peak)
                np.random.normal(loc=90, scale=6, size=200),  # high performers (upper peak)
            ]
        )
    }
)

# Plot: reads only df and the constants above
scores = df[SCORE].dropna()
x_range = np.linspace(scores.min() - 5, scores.max() + 5, 200)
kde = stats.gaussian_kde(scores)

fig = go.Figure()

# Histogram normalized to probability density (bar areas sum to 1)
fig.add_trace(
    go.Histogram(
        x=scores,
        histnorm="probability density",
        nbinsx=30,
        marker={"color": IMPRINT_PALETTE[0], "line": {"color": PAGE_BG, "width": 0.5}},
        opacity=0.75,
        name="Histogram (density)",
        hovertemplate="<b>Score range</b>: %{x:.1f}<br><b>Density</b>: %{y:.4f}<extra></extra>",
    )
)

# Kernel density estimate on the same density scale
fig.add_trace(
    go.Scatter(
        x=x_range,
        y=kde(x_range),
        mode="lines",
        line={"color": IMPRINT_PALETTE[1], "width": 2.5},
        name="Density curve (KDE)",
        hovertemplate="<b>Score</b>: %{x:.1f}<br><b>Density</b>: %{y:.4f}<extra></extra>",
    )
)

# Style
axis_style = {
    "tickfont": {"size": 10, "color": INK_SOFT},
    "showgrid": True,
    "gridcolor": GRID,
    "gridwidth": 1,
    "linecolor": INK_SOFT,
    "zerolinecolor": INK_SOFT,
}
fig.update_layout(
    autosize=False,
    title={
        "text": "histogram-density · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"title": {"text": SCORE, "font": {"size": 12, "color": INK}}, **axis_style},
    yaxis={"title": {"text": "Density (probability per unit)", "font": {"size": 12, "color": INK}}, **axis_style},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "font": {"size": 11, "color": INK_SOFT},
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    bargap=0,
    hovermode="closest",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
