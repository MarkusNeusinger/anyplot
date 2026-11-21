"""anyplot.ai
histogram-stepwise: Step Histogram
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 32  # bins shared by every distribution

# Columns: set these to your table's column names
VALUES = ["Value"]  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("values.csv")
np.random.seed(42)
df = pd.DataFrame({VALUES[0]: np.random.normal(loc=100, scale=18, size=1200)})

# Plot: reads only df and the constants above
series = df[VALUES[0]].dropna()
edges = np.histogram_bin_edges(series, bins=N_BINS)
counts, _ = np.histogram(series, bins=edges)

# Step outline: each bin rises from the baseline, runs across at its count, and drops back
x_coords = np.repeat(edges[:-1], 4)
x_coords[2::4] = edges[1:]
x_coords[3::4] = edges[1:]
y_coords = np.zeros(len(counts) * 4)
y_coords[1::4] = counts
y_coords[2::4] = counts

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=x_coords,
        y=y_coords,
        mode="lines",
        line={"color": IMPRINT_PALETTE[0], "width": 3},
        hovertemplate=f"{VALUES[0]}: %{{x:.1f}}<br>Frequency: %{{y}}<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    title={"text": "histogram-stepwise · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}},
    xaxis={
        "title": {"text": VALUES[0], "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Frequency", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "rangemode": "tozero",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    hovermode="closest",
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    showlegend=False,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
