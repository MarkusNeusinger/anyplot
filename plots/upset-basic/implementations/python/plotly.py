"""anyplot.ai
upset-basic: UpSet Plot for Multi-Set Intersection Analysis
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Created: 2026-05-13
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
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
DOT_INACTIVE = "rgba(150,148,140,0.35)" if THEME == "light" else "rgba(140,138,130,0.40)"

# Imprint palette: the first position carries the single series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
TOP_N = 15  # number of intersections shown, largest first

# Columns: set these to your table's column names
CUSTOMER = "Customer"  # role: element
SEGMENT = "Segment"  # role: sets

# Data: replace this block with your own table, for example df = pd.read_csv("memberships.csv")
# One row per customer-segment membership; a customer in three segments has three rows.
rng = np.random.default_rng(42)
segment_share = {
    "Newsletter": 0.52,
    "Mobile app": 0.44,
    "Loyalty club": 0.37,
    "Premium tier": 0.29,
    "Referred": 0.23,
    "Gift buyers": 0.17,
}
n_customers = 1200
member = rng.random((n_customers, len(segment_share))) < np.array(list(segment_share.values()))
rows, cols = np.nonzero(member)
df = pd.DataFrame({CUSTOMER: [f"C{i:04d}" for i in rows], SEGMENT: [list(segment_share)[j] for j in cols]})

# Plot: reads only df and the constants above
membership = pd.crosstab(df[CUSTOMER], df[SEGMENT]).gt(0)
set_sizes = membership.sum().sort_values()  # ascending: the largest set sits at the top of the matrix
set_names = list(set_sizes.index)
n_sets = len(set_names)
membership = membership[set_names]

combos = membership.value_counts().head(TOP_N)  # exact combination -> number of customers
inter_patterns = [tuple(bool(v) for v in key) for key in combos.index]
inter_sizes = combos.to_numpy()
n_inter = len(inter_patterns)

# Dot matrix and connecting lines
active_x, active_y, inactive_x, inactive_y = [], [], [], []
line_x, line_y = [], []
for col_i, pattern in enumerate(inter_patterns):
    active_rows = [r for r, m in enumerate(pattern) if m]
    for r, m in enumerate(pattern):
        (active_x if m else inactive_x).append(col_i)
        (active_y if m else inactive_y).append(r)
    if len(active_rows) > 1:
        line_x.extend([col_i, col_i, None])
        line_y.extend([min(active_rows), max(active_rows), None])

# 2x2 grid: [empty | intersection bars] / [set bars | dot matrix]
fig = make_subplots(
    rows=2,
    cols=2,
    row_heights=[0.55, 0.45],
    column_widths=[0.2, 0.8],
    shared_xaxes=True,  # links (1,2) and (2,2) x-axes so bars align with matrix columns
    vertical_spacing=0.03,
    horizontal_spacing=0.17,
)

fig.add_trace(
    go.Bar(
        x=list(range(n_inter)),
        y=inter_sizes,
        marker_color=BRAND,
        marker_line_width=0,
        hovertemplate="%{y} customers<extra></extra>",
    ),
    row=1,
    col=2,
)

fig.add_trace(
    go.Bar(
        x=set_sizes.to_numpy(),
        y=list(range(n_sets)),
        orientation="h",
        marker_color=BRAND,
        marker_line_width=0,
        customdata=set_names,
        hovertemplate="%{customdata}: %{x} customers<extra></extra>",
    ),
    row=2,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=inactive_x, y=inactive_y, mode="markers", marker={"color": DOT_INACTIVE, "size": 13}, hoverinfo="skip"
    ),
    row=2,
    col=2,
)
fig.add_trace(
    go.Scatter(x=line_x, y=line_y, mode="lines", line={"color": BRAND, "width": 3}, hoverinfo="skip"), row=2, col=2
)
fig.add_trace(
    go.Scatter(x=active_x, y=active_y, mode="markers", marker={"color": BRAND, "size": 13}, hoverinfo="skip"),
    row=2,
    col=2,
)

# Style
title = "Customer Segment Overlap · upset-basic · plotly · anyplot.ai"
title_size = round(16 * min(1.0, 67 / len(title)))
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK, "size": 10},
    title={"text": title, "font": {"size": title_size, "color": INK}, "x": 0.5, "xanchor": "center"},
    showlegend=False,
    bargap=0.35,
    margin={"l": 30, "r": 30, "t": 60, "b": 40},
)

# Empty top-left panel: no chrome
fig.update_xaxes(visible=False, row=1, col=1)
fig.update_yaxes(visible=False, row=1, col=1)

# Intersection bars: count axis on y, columns shared with the matrix
fig.update_yaxes(
    title={"text": "Intersection size (customers)", "font": {"size": 12, "color": INK}},
    tickfont={"size": 10, "color": INK_SOFT},
    gridcolor=GRID,
    zeroline=False,
    showline=False,
    rangemode="tozero",
    row=1,
    col=2,
)
fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, showline=False, row=1, col=2)

# Set size bars: reversed x so bars grow toward the matrix
fig.update_xaxes(
    autorange="reversed",
    title={"text": "Set size (customers)", "font": {"size": 12, "color": INK}},
    tickfont={"size": 10, "color": INK_SOFT},
    gridcolor=GRID,
    zeroline=False,
    showline=False,
    rangemode="tozero",
    row=2,
    col=1,
)
fig.update_yaxes(
    showticklabels=False, showgrid=False, zeroline=False, showline=False, range=[-0.5, n_sets - 0.5], row=2, col=1
)

# Dot matrix: segment names label the rows
fig.update_xaxes(
    showgrid=False, zeroline=False, showticklabels=False, showline=False, range=[-0.5, n_inter - 0.5], row=2, col=2
)
fig.update_yaxes(
    tickmode="array",
    tickvals=list(range(n_sets)),
    ticktext=set_names,
    tickfont={"size": 11, "color": INK_SOFT},
    showgrid=False,
    zeroline=False,
    showline=False,
    range=[-0.5, n_sets - 0.5],
    row=2,
    col=2,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
