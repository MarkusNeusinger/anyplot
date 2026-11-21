"""anyplot.ai
histogram-stacked: Stacked Histogram
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-12
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
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 20  # one shared set of bin edges for every group

# Columns: set these to your table's column names
WEIGHT = "Product weight (g)"  # role: values
LINE = "Production line"  # role: group
COUNT = "Frequency"  # derived by the plot code: observations per bin

# Data: replace this block with your own table, for example df = pd.read_csv("weights.csv")
np.random.seed(42)
n_per_group = 150
line_a = np.random.normal(loc=250, scale=30, size=n_per_group)
line_b = np.random.normal(loc=280, scale=25, size=n_per_group)
line_c = np.random.normal(loc=260, scale=35, size=n_per_group)
df = pd.DataFrame(
    {
        WEIGHT: np.concatenate([line_a, line_b, line_c]),
        LINE: ["Line A"] * n_per_group + ["Line B"] * n_per_group + ["Line C"] * n_per_group,
    }
)

# Plot: reads only df and the constants above
bin_edges = np.histogram_bin_edges(df[WEIGHT].dropna(), bins=N_BINS)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
bin_width = bin_edges[1] - bin_edges[0]

fig = go.Figure()
for i, (line, rows) in enumerate(df.groupby(LINE, sort=False)):
    counts, _ = np.histogram(rows[WEIGHT].dropna(), bins=bin_edges)
    fig.add_trace(
        go.Bar(
            x=bin_centers,
            y=counts,
            name=str(line),
            marker={"color": IMPRINT_PALETTE[i], "line": {"color": PAGE_BG, "width": 0.8}},
            width=bin_width,
            hovertemplate=f"<b>{line}</b><br>{WEIGHT}: %{{x:.1f}}<br>{COUNT}: %{{y}}<extra></extra>",
        )
    )

# Style
title = "histogram-stacked · python · plotly · anyplot.ai"
fig.update_layout(
    autosize=False,
    title={"text": title, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": WEIGHT, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": COUNT, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    barmode="stack",
    bargap=0,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "title": {"text": LINE, "font": {"size": 10, "color": INK_SOFT}},
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
