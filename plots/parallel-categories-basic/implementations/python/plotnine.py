"""anyplot.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-13
"""

import os
import sys


# Prevent current directory from shadowing the plotnine package
sys.path = [p for p in sys.path if not p.endswith("implementations") and not p.endswith("python")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_label,
    geom_polygon,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DIMENSIONS = ["Channel", "Product", "Customer", "Outcome"]  # role: dimension_ (left to right)
COUNT = "Sessions"  # role: count
COLOR_BY = DIMENSIONS[-1]  # the dimension that colors the ribbons

# Data: replace this block with your own table, for example df = pd.read_csv("journeys.csv")
# Customer journeys: purchase channel -> product -> customer type -> outcome.
# Per (channel, product): sessions of returning-purchased, returning-abandoned, new-purchased, new-abandoned.
journeys = {
    ("Online", "Electronics"): (187, 42, 145, 98),
    ("Online", "Clothing"): (156, 38, 112, 76),
    ("Online", "Home"): (89, 23, 67, 54),
    ("Store", "Electronics"): (124, 18, 78, 32),
    ("Store", "Clothing"): (142, 15, 95, 28),
    ("Store", "Home"): (78, 12, 56, 21),
    ("Mobile", "Electronics"): (134, 67, 89, 112),
    ("Mobile", "Clothing"): (118, 52, 76, 94),
    ("Mobile", "Home"): (67, 34, 45, 58),
}
rows = []
for (channel, product), counts in journeys.items():
    for (customer, outcome), count in zip(
        [("Returning", "Purchased"), ("Returning", "Abandoned"), ("New", "Purchased"), ("New", "Abandoned")],
        counts,
        strict=True,
    ):
        rows.append((channel, product, customer, outcome, count))
df = pd.DataFrame(rows, columns=[*DIMENSIONS, COUNT])

# Plot: reads only df and the constants above
n_dims = len(DIMENSIONS)
x_axes = np.linspace(0.19, 0.74, n_dims)
node_width = 0.035
node_gap = 0.03
total_height = 0.82
y_top0 = 0.92

# Category order per dimension is the data's order of first appearance
categories = {dim: df[dim].unique().tolist() for dim in DIMENSIONS}

# Nodes: one segment per category, its height is the category's share of all observations
grand_total = df[COUNT].sum()
node_rows = []
nodes = {}
for d, dim in enumerate(DIMENSIONS):
    totals = df.groupby(dim, sort=False)[COUNT].sum()
    cursor = y_top0
    for cat in categories[dim]:
        height = totals[cat] / grand_total * total_height
        nodes[(d, cat)] = {"top": cursor, "height": height, "out": 0.0, "in": 0.0}
        node_rows.append(
            {
                "xmin": x_axes[d] - node_width / 2,
                "xmax": x_axes[d] + node_width / 2,
                "ymin": cursor - height,
                "ymax": cursor,
                "x": x_axes[d],
                "y": cursor - height / 2,
                "y_below": cursor - height - node_gap / 2,
                "label": f"{cat} ({int(totals[cat])})",
                "count": int(totals[cat]),
                "dim_idx": d,
            }
        )
        cursor -= height + node_gap
nodes_df = pd.DataFrame(node_rows)

# Ribbons between neighbouring axes, width proportional to the sessions sharing both categories.
# Stacked inside each segment in the order of the partner axis, so ribbons do not cross within a pair.
t = np.linspace(0, 1, 30)
ease = 3 * t**2 - 2 * t**3
ribbon_rows = []
ribbon_id = 0
for d in range(n_dims - 1):
    left, right = DIMENSIONS[d], DIMENSIONS[d + 1]
    keys = list(dict.fromkeys([left, right, COLOR_BY]))
    pair = df.groupby(keys, sort=False)[COUNT].sum().reset_index()
    pair["l_rank"] = pair[left].map({c: i for i, c in enumerate(categories[left])})
    pair["r_rank"] = pair[right].map({c: i for i, c in enumerate(categories[right])})
    # Stack order differs at each end: sources by target rank, targets by source rank
    src_order = pair.sort_values(["l_rank", "r_rank"])
    src_pos = {}
    for _, r in src_order.iterrows():
        node = nodes[(d, r[left])]
        h = r[COUNT] / grand_total * total_height
        src_pos[(r[left], r[right], r[COLOR_BY])] = node["top"] - node["out"]
        node["out"] += h
    tgt_pos = {}
    for _, r in pair.sort_values(["r_rank", "l_rank"]).iterrows():
        node = nodes[(d + 1, r[right])]
        h = r[COUNT] / grand_total * total_height
        tgt_pos[(r[left], r[right], r[COLOR_BY])] = node["top"] - node["in"]
        node["in"] += h
    for _, r in pair.iterrows():
        key = (r[left], r[right], r[COLOR_BY])
        h = r[COUNT] / grand_total * total_height
        y0, y1 = src_pos[key], tgt_pos[key]
        x_curve = np.linspace(x_axes[d] + node_width / 2, x_axes[d + 1] - node_width / 2, len(t))
        upper = y0 + (y1 - y0) * ease
        lower = upper - h
        xs = np.concatenate([x_curve, x_curve[::-1]])
        ys = np.concatenate([upper, lower[::-1]])
        for x, y in zip(xs, ys, strict=True):
            ribbon_rows.append({"x": x, "y": y, "ribbon": ribbon_id, "color_group": r[COLOR_BY]})
        ribbon_id += 1
ribbons_df = pd.DataFrame(ribbon_rows)

# Axis titles above the first node row; category labels outside the end axes, below the middle ones
titles_df = pd.DataFrame({"x": x_axes, "y": y_top0 + 0.06, "label": DIMENSIONS})
first = nodes_df[nodes_df["dim_idx"] == 0].assign(label_x=lambda n: n["xmin"] - 0.012)
last = nodes_df[nodes_df["dim_idx"] == n_dims - 1].assign(label_x=lambda n: n["xmax"] + 0.012)
middle = nodes_df[(nodes_df["dim_idx"] > 0) & (nodes_df["dim_idx"] < n_dims - 1)].assign(
    label_x=lambda n: n["xmax"] + 0.008
)

title = "parallel-categories-basic · python · plotnine · anyplot.ai"

plot = (
    ggplot()
    + geom_polygon(ribbons_df, aes(x="x", y="y", group="ribbon", fill="color_group"), alpha=0.55)
    + geom_rect(
        nodes_df, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill=INK_SOFT, color=PAGE_BG, size=0.4
    )
    + geom_text(titles_df, aes(x="x", y="y", label="label"), size=10, color=INK, fontweight="bold")
    + geom_text(first, aes(x="label_x", y="y", label="label"), size=8, color=INK_SOFT, ha="right")
    + geom_text(last, aes(x="label_x", y="y", label="label"), size=8, color=INK_SOFT, ha="left")
    + geom_label(
        middle,
        aes(x="label_x", y="y", label="label"),
        size=8,
        color=INK,
        fill=PAGE_BG,
        alpha=0.85,
        label_size=0,
        ha="left",
    )
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=df[COLOR_BY].unique().tolist())
    + scale_x_continuous(limits=(0, 1), expand=(0, 0))
    + scale_y_continuous(limits=(0.02, 1.02), expand=(0, 0))
    + labs(title=title, x="", y="", fill=COLOR_BY)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_title=element_text(size=10, weight="bold", color=INK),
        legend_text=element_text(size=9, color=INK_SOFT),
        legend_position="right",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
