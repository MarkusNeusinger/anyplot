"""anyplot.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_size_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per level in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
EMPLOYEE = "Employee"  # role: nodes
LEVEL = "Level"  # role: level
MANAGER = "Reports to"  # role: edges

# Data: replace this block with your own table, for example df = pd.read_csv("org.csv")
# Small tech company organizational chart: 30 employees across 4 levels, one row per employee
df = pd.DataFrame(
    {
        EMPLOYEE: [
            "CEO",
            "VP Eng",
            "VP Sales",
            "VP Ops",
            "Mgr FE",
            "Mgr BE",
            "Mgr QA",
            "Mgr West",
            "Mgr East",
            "Mgr HR",
            "Mgr IT",
            "Mgr Fin",
            "Dev 1",
            "Dev 2",
            "Dev 3",
            "Dev 4",
            "Dev 5",
            "Dev 6",
            "QA 1",
            "QA 2",
            "Rep 1",
            "Rep 2",
            "Rep 3",
            "Rep 4",
            "Rep 5",
            "HR 1",
            "IT 1",
            "IT 2",
            "Fin 1",
            "Fin 2",
        ],
        LEVEL: ["Executive"] + ["VP"] * 3 + ["Manager"] * 8 + ["Staff"] * 18,
        MANAGER: [None]
        + ["CEO"] * 3
        + ["VP Eng"] * 3
        + ["VP Sales"] * 2
        + ["VP Ops"] * 3
        + ["Mgr FE"] * 3
        + ["Mgr BE"] * 3
        + ["Mgr QA"] * 2
        + ["Mgr West"] * 2
        + ["Mgr East"] * 3
        + ["Mgr HR"]
        + ["Mgr IT"] * 2
        + ["Mgr Fin"] * 2,
    }
)

# Plot: reads only df and the constants above
parent_of = dict(zip(df[EMPLOYEE], df[MANAGER], strict=True))
children = {name: [] for name in df[EMPLOYEE]}
for name, boss in parent_of.items():
    if pd.notna(boss):
        children[boss].append(name)
root = next(name for name, boss in parent_of.items() if pd.isna(boss))


def count_leaves(name):
    """Count leaf nodes in the subtree below a node."""
    if not children[name]:
        return 1
    return sum(count_leaves(c) for c in children[name])


x_pos = {}
depth = {}


def assign_layout(name, left, right, level):
    """Give each node a column within [left, right] and center parents over their children."""
    depth[name] = level
    if not children[name]:
        x_pos[name] = (left + right) / 2
        return
    total = count_leaves(name)
    cursor = left
    for child in children[name]:
        width = (right - left) * count_leaves(child) / total
        assign_layout(child, cursor, cursor + width, level + 1)
        cursor += width
    child_x = [x_pos[c] for c in children[name]]
    x_pos[name] = (min(child_x) + max(child_x)) / 2


assign_layout(root, 0, 1, 0)
max_depth = max(depth.values())

nodes = df.copy()
nodes["x"] = nodes[EMPLOYEE].map(x_pos)
nodes["y"] = 1 - nodes[EMPLOYEE].map(depth) / max_depth
nodes["size"] = 9 - nodes[EMPLOYEE].map(depth) * 1.5
nodes["label_y"] = nodes["y"] + 0.04

edges = nodes[nodes[MANAGER].notna()].copy()
edges["xend"] = edges["x"]
edges["yend"] = edges["y"]
edges["x"] = edges[MANAGER].map(x_pos)
edges["y"] = 1 - edges[MANAGER].map(depth) / max_depth

plot = (
    ggplot()
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=edges, color=INK_SOFT, size=0.6, alpha=0.6)
    + geom_point(aes(x="x", y="y", color=LEVEL, size="size"), data=nodes, stroke=1, alpha=0.95)
    + geom_text(aes(x="x", y="label_y", label=EMPLOYEE), data=nodes, size=4, color=INK, fontface="bold")
    + scale_color_manual(values=IMPRINT_PALETTE)
    + scale_size_identity()
    + scale_x_continuous(limits=(-0.05, 1.05))
    + scale_y_continuous(limits=(-0.08, 1.12))
    + labs(title="network-hierarchical · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, face="bold", color=INK),
        legend_position="right",
    )
)

# Save as PNG (scale 4x to get 3200 x 1800 px) and interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
