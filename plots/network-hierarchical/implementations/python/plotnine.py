"""anyplot.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_size_identity,
    theme,
    xlim,
    ylim,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per hierarchy level in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
NODE = "Employee"  # role: nodes
PARENT = "Reports to"  # role: edges
LEVEL = "Hierarchy level"  # role: level

# Data: replace this block with your own table, for example df = pd.read_csv("org.csv")
# One row per node, listed level by level; the root has no parent.
df = pd.DataFrame(
    {
        NODE: [
            "CEO",
            "VP Engineering",
            "VP Product",
            "VP Operations",
            "Frontend Dir",
            "Backend Dir",
            "PM Lead",
            "UX Lead",
            "IT Manager",
            "HR Manager",
            "FE Dev 1",
            "FE Dev 2",
            "BE Dev 1",
            "BE Dev 2",
            "PM 1",
            "Designer",
            "UX Rsrch",
            "SysAdmin",
            "DevOps",
            "Recruiter",
            "Payroll",
            "Benefits",
        ],
        PARENT: [
            None,
            "CEO",
            "CEO",
            "CEO",
            "VP Engineering",
            "VP Engineering",
            "VP Product",
            "VP Product",
            "VP Operations",
            "VP Operations",
            "Frontend Dir",
            "Frontend Dir",
            "Backend Dir",
            "Backend Dir",
            "PM Lead",
            "UX Lead",
            "UX Lead",
            "IT Manager",
            "IT Manager",
            "HR Manager",
            "HR Manager",
            "HR Manager",
        ],
    }
)

# Plot: tree layout computed from the parent column
depth = {}
for node, parent in zip(df[NODE], df[PARENT], strict=True):
    depth[node] = 0 if pd.isna(parent) else depth[parent] + 1
df[LEVEL] = ["Level " + str(depth[node]) for node in df[NODE]]
max_depth = max(depth.values())

# Each level spreads evenly across the width, in listed order
x_pos = {}
for d in range(max_depth + 1):
    row = [node for node in df[NODE] if depth[node] == d]
    for i, node in enumerate(row):
        x_pos[node] = 0.5 if len(row) == 1 else 0.05 + i * 0.90 / (len(row) - 1)
y_pos = {node: 0.90 - d * 0.22 for node, d in depth.items()}

df["x"] = df[NODE].map(x_pos)
df["y"] = df[NODE].map(y_pos)
df["size"] = df[NODE].map(lambda node: max(3.0, 9.0 - 1.6 * depth[node]))

# Edges: one segment from each parent to its child
edge_df = df.dropna(subset=[PARENT]).copy()
edge_df["xend"] = edge_df["x"]
edge_df["yend"] = edge_df["y"]
edge_df["x"] = edge_df[PARENT].map(x_pos)
edge_df["y"] = edge_df[PARENT].map(y_pos)

is_leaf = ~df[NODE].isin(df[PARENT])
levels = df[LEVEL].unique().tolist()
title = "network-hierarchical · python · plotnine · anyplot.ai"

plot = (
    ggplot()
    # Edges first, thin and soft, underneath the nodes
    + geom_segment(
        data=edge_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=INK_SOFT, size=0.5, alpha=0.7
    )
    # Nodes colored by hierarchy level, larger toward the root
    + geom_point(data=df, mapping=aes(x="x", y="y", color=LEVEL, size="size"), alpha=0.95, stroke=0.25)
    # Labels: above internal nodes, below leaves, so edges leaving a node never cross its label
    + geom_text(
        data=df[~is_leaf], mapping=aes(x="x", y="y", label=NODE), size=3.6, va="bottom", nudge_y=0.035, color=INK
    )
    + geom_text(data=df[is_leaf], mapping=aes(x="x", y="y", label=NODE), size=3.6, va="top", nudge_y=-0.035, color=INK)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=levels)
    + scale_size_identity()
    + labs(title=title, color=LEVEL)
    + xlim(-0.02, 1.02)
    + ylim(0.90 - max_depth * 0.22 - 0.12, 1.0)
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=12, ha="center", color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_position="bottom",
        legend_key=element_rect(fill=ELEVATED_BG),
        # No axes or grid on a network
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
