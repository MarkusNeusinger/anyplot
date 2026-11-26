"""anyplot.ai
histogram-basic: Basic Histogram
Library: plotly 6.7.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-28
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 20  # number of equal-width bins

# Columns: set these to your table's column names
SCORE = "Score (points)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
scores_main = np.random.normal(loc=72, scale=10, size=180)
scores_high = np.random.normal(loc=88, scale=5, size=40)
scores_low = np.random.normal(loc=45, scale=4, size=15)
df = pd.DataFrame({SCORE: np.clip(np.concatenate([scores_main, scores_high, scores_low]), 0, 100)})

# Plot
fig = go.Figure()
fig.add_trace(
    go.Histogram(
        x=df[SCORE],
        nbinsx=N_BINS,
        marker={"color": IMPRINT_PALETTE[0], "line": {"color": PAGE_BG, "width": 1}},
        hovertemplate=f"{SCORE}: %{{x}}<br>Count: %{{y}}<extra></extra>",
    )
)

title = "histogram-basic · python · plotly · anyplot.ai"

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={"text": title, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": SCORE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "zeroline": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "linewidth": 1,
    },
    yaxis={
        "title": {"text": "Frequency (count)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "griddash": "dot",
        "zeroline": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "linewidth": 1,
        "rangemode": "tozero",
    },
    template="plotly_white",
    bargap=0,
    margin={"l": 80, "r": 40, "t": 60, "b": 60},
)

# Save — 3200×1800 px landscape
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
