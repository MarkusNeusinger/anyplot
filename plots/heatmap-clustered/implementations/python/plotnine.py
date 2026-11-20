"""anyplot.ai
heatmap-clustered: Clustered Heatmap
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_rect,
    element_text,
    geom_segment,
    geom_text,
    geom_tile,
    ggplot,
    guide_colorbar,
    guides,
    labs,
    scale_fill_gradient2,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy.cluster.hierarchy import dendrogram, linkage


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: diverging ends and the theme-adaptive midpoint
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
DIV_LOW, DIV_HIGH = IMPRINT_PALETTE[4], IMPRINT_PALETTE[2]
DIV_MID = "#FAF8F1" if THEME == "light" else "#1A1A17"

# Constants
CLUSTER_METHOD = "ward"  # Ward linkage on Euclidean distance, the spec's common default

# Columns: set these to your table's column names
CUSTOMER = "Customer"  # role: row_labels
VALUE = "Z-score vs. all customers"  # role: matrix

# Data: replace this block with your own long table, for example df = pd.read_csv("behavior.csv")
# Customer segmentation: 24 customers x 12 standardized behavior metrics, three hidden segments
rng = np.random.default_rng(42)
metrics = [
    "Order frequency",
    "Basket size",
    "Loyalty points",
    "Premium share",
    "Discount usage",
    "Cart abandonment",
    "Coupon redemption",
    "Return rate",
    "Email opens",
    "App sessions",
    "Weekend share",
    "Support tickets",
]
segment_profiles = np.array(
    [
        [1.6, 1.4, 1.5, 1.3, -1.2, -0.9, -1.0, -0.6, 0.4, 0.8, 0.0, -0.5],  # loyal big spenders
        [0.0, -1.1, -0.5, -1.4, 1.7, 1.2, 1.6, 0.9, 0.3, -0.2, 0.5, 0.2],  # bargain hunters
        [-1.5, -0.6, -1.2, -0.3, -0.4, 0.6, -0.5, 0.0, -1.2, 1.4, 1.2, 1.1],  # casual browsers
    ]
)
segment_of = rng.permutation(np.repeat([0, 1, 2], [9, 8, 7]))
values = segment_profiles[segment_of] + rng.normal(0, 0.45, size=(len(segment_of), len(metrics)))
customers = [f"C{i + 1:02d}" for i in range(len(segment_of))]
df = pd.DataFrame(values.round(2), index=pd.Index(customers, name=CUSTOMER), columns=metrics)

# Plot: reads only df and the constants above
table = df
row_link = linkage(table.to_numpy(), method=CLUSTER_METHOD)
col_link = linkage(table.to_numpy().T, method=CLUSTER_METHOD)
row_dend = dendrogram(row_link, no_plot=True)
col_dend = dendrogram(col_link, no_plot=True)
table = table.iloc[row_dend["leaves"], col_dend["leaves"]]
n_rows, n_cols = table.shape

# One unit per cell; the heatmap spans x 0..n_cols and y 0..n_rows, first leaf at the top
dend_w = 0.28 * n_cols  # row dendrogram width
dend_h = 0.22 * n_rows  # column dendrogram height
gap = 0.4

tiles = pd.DataFrame(
    {
        "x": np.tile(np.arange(n_cols) + 0.5, n_rows),
        "y": np.repeat(n_rows - np.arange(n_rows) - 0.5, n_cols),
        "value": table.to_numpy().ravel(),
    }
)


def branches(dend, link, horizontal):
    """Turn scipy's dendrogram coordinates into segments in heatmap units."""
    n_leaves = len(dend["leaves"])
    top = link[:, 2].max()
    rows = []
    for leaf_pos, height in zip(dend["icoord"], dend["dcoord"], strict=True):
        pos = [(p - 5) / 10 + 0.5 for p in leaf_pos]
        dist = [h / top for h in height]
        for k in range(3):
            if horizontal:  # row tree: leaves on y (top-down), distance grows leftwards
                rows.append(
                    {
                        "x": -gap - dist[k] * dend_w,
                        "xend": -gap - dist[k + 1] * dend_w,
                        "y": n_leaves - pos[k],
                        "yend": n_leaves - pos[k + 1],
                    }
                )
            else:  # column tree: leaves on x, distance grows upwards
                rows.append(
                    {
                        "x": pos[k],
                        "xend": pos[k + 1],
                        "y": n_rows + gap + dist[k] * dend_h,
                        "yend": n_rows + gap + dist[k + 1] * dend_h,
                    }
                )
    return pd.DataFrame(rows)


row_segments = branches(row_dend, row_link, horizontal=True)
col_segments = branches(col_dend, col_link, horizontal=False)

row_labels = pd.DataFrame({"x": n_cols + 0.3, "y": n_rows - np.arange(n_rows) - 0.5, "label": table.index.tolist()})
col_labels = pd.DataFrame({"x": np.arange(n_cols) + 0.5, "y": -0.3, "label": table.columns.tolist()})

title = "heatmap-clustered · python · plotnine · anyplot.ai"
limit = np.abs(table.to_numpy()).max()

plot = (
    ggplot()
    + geom_tile(aes(x="x", y="y", fill="value"), data=tiles, width=0.96, height=0.96)
    + geom_segment(aes(x="x", xend="xend", y="y", yend="yend"), data=row_segments, color=INK_SOFT, size=0.5)
    + geom_segment(aes(x="x", xend="xend", y="y", yend="yend"), data=col_segments, color=INK_SOFT, size=0.5)
    + geom_text(aes(x="x", y="y", label="label"), data=row_labels, ha="left", size=6.5, color=INK_SOFT)
    + geom_text(
        aes(x="x", y="y", label="label"), data=col_labels, ha="right", va="top", size=6.5, color=INK_SOFT, angle=45
    )
    + scale_fill_gradient2(low=DIV_LOW, mid=DIV_MID, high=DIV_HIGH, midpoint=0, limits=(-limit, limit), name=VALUE)
    + guides(fill=guide_colorbar(nbin=64, theme=theme(legend_title_position="top")))
    + scale_x_continuous(breaks=[], expand=(0, 0))
    + scale_y_continuous(breaks=[], expand=(0, 0))
    + coord_cartesian(xlim=(-gap - dend_w - 0.3, n_cols + 2.6), ylim=(-6.2, n_rows + gap + dend_h + 0.3), expand=False)
    + labs(x="", y="", title=title)
    + theme_minimal()
    + theme(
        figure_size=(6, 6),
        text=element_text(size=8),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=13, ha="center", color=INK),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        legend_position="bottom",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_key_width=200,
        legend_key_height=10,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
