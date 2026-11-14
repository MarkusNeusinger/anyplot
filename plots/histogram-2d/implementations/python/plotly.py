"""anyplot.ai
histogram-2d: 2D Histogram Heatmap
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-08
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: first position for the single-series marginals
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [[0.0, "#009E73"], [1.0, "#4467A3"]]  # sequential density scale

# Constants
N_BINS = 40  # bins per axis

# Columns: set these to your table's column names
AGE = "Customer Age (years)"  # role: x
PURCHASES = "Annual Purchases (count)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("customers.csv")
np.random.seed(42)
mean = [45, 25]  # mean age and mean purchases per year
cov = [[150, 35], [35, 120]]  # positive correlation (0.6)
sample = np.random.multivariate_normal(mean, cov, 5000)
df = pd.DataFrame({AGE: np.clip(sample[:, 0], 18, 85), PURCHASES: np.clip(sample[:, 1], 0, 80)})

# Plot: reads only df and the constants above
x_bins = dict(start=df[AGE].min(), end=df[AGE].max(), size=(df[AGE].max() - df[AGE].min()) / N_BINS)
y_bins = dict(
    start=df[PURCHASES].min(), end=df[PURCHASES].max(), size=(df[PURCHASES].max() - df[PURCHASES].min()) / N_BINS
)

observed = df.dropna(subset=[AGE, PURCHASES])
counts, x_edges, y_edges = np.histogram2d(observed[AGE], observed[PURCHASES], bins=N_BINS)
counts = np.where(counts > 0, counts, np.nan).T  # empty bins stay blank
x_centers = (x_edges[:-1] + x_edges[1:]) / 2
y_centers = (y_edges[:-1] + y_edges[1:]) / 2

fig = make_subplots(
    rows=2,
    cols=2,
    column_widths=[0.85, 0.15],
    row_heights=[0.15, 0.85],
    horizontal_spacing=0.01,
    vertical_spacing=0.015,
    shared_xaxes=True,
    shared_yaxes=True,
    specs=[[{"type": "histogram"}, None], [{"type": "heatmap"}, {"type": "histogram"}]],
)

# Main 2D histogram heatmap
fig.add_trace(
    go.Heatmap(
        x=x_centers,
        y=y_centers,
        z=counts,
        colorscale=IMPRINT_SEQ,
        xgap=1,
        ygap=1,
        colorbar=dict(
            title=dict(text="Count", font=dict(size=12, color=INK)),
            tickfont=dict(size=10, color=INK_SOFT),
            outlinecolor=INK_SOFT,
            len=0.7,
            y=0.36,
            yanchor="middle",
            thickness=14,
        ),
    ),
    row=2,
    col=1,
)

# Marginal histogram for age (top), same bins as the heatmap
fig.add_trace(
    go.Histogram(x=df[AGE], xbins=x_bins, marker=dict(color=IMPRINT_PALETTE[0], line=dict(width=0)), showlegend=False),
    row=1,
    col=1,
)

# Marginal histogram for purchases (right), same bins as the heatmap
fig.add_trace(
    go.Histogram(
        y=df[PURCHASES], ybins=y_bins, marker=dict(color=IMPRINT_PALETTE[0], line=dict(width=0)), showlegend=False
    ),
    row=2,
    col=2,
)

fig.update_layout(
    autosize=False,
    margin=dict(l=80, r=40, t=60, b=60),
    title=dict(
        text="histogram-2d · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    bargap=0.02,
)

# Main axes carry the labels
fig.update_xaxes(
    title=dict(text=AGE, font=dict(size=12, color=INK)),
    tickfont=dict(size=10, color=INK_SOFT),
    gridcolor=GRID,
    linecolor=INK_SOFT,
    row=2,
    col=1,
)
fig.update_yaxes(
    title=dict(text=PURCHASES, font=dict(size=12, color=INK)),
    tickfont=dict(size=10, color=INK_SOFT),
    gridcolor=GRID,
    linecolor=INK_SOFT,
    row=2,
    col=1,
)

# Marginal axes stay quiet
for r, c in [(1, 1), (2, 2)]:
    fig.update_xaxes(showticklabels=False, gridcolor=GRID, linecolor=INK_SOFT, row=r, col=c)
    fig.update_yaxes(showticklabels=False, gridcolor=GRID, linecolor=INK_SOFT, row=r, col=c)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
