"""anyplot.ai
network-directed: Directed Network Graph
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    arrow,
    element_rect,
    element_text,
    geom_label,
    geom_point,
    geom_segment,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
    xlim,
    ylim,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per node group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
EDGES = ["Source", "Target"]  # role: edges
NODES = ["Module", "Module type"]  # role: nodes
SOURCE, TARGET = EDGES
LABEL, GROUP = NODES

# Data: replace this block with your own edge list (df) and node table (nodes),
# for example df = pd.read_csv("edges.csv")
nodes = pd.DataFrame(
    {
        LABEL: ["App", "API", "Auth", "Database", "Cache", "Config", "Logger", "Utils", "HTTP Client", "Queue"],
        GROUP: ["Application", "Core", "Core", "Core"]
        + ["Infrastructure", "Utility", "Utility", "Utility", "Infrastructure", "Infrastructure"],
    }
)
df = pd.DataFrame(
    [
        ("App", "API"),
        ("App", "Config"),
        ("API", "Auth"),
        ("API", "Database"),
        ("API", "Cache"),
        ("API", "Logger"),
        ("Auth", "Database"),
        ("Auth", "Config"),
        ("Auth", "Logger"),
        ("Database", "Config"),
        ("Database", "Logger"),
        ("Cache", "Config"),
        ("Cache", "Logger"),
        ("HTTP Client", "Config"),
        ("HTTP Client", "Logger"),
        ("Queue", "Config"),
        ("Queue", "Logger"),
        ("API", "HTTP Client"),
        ("API", "Queue"),
        ("Utils", "Logger"),
    ],
    columns=[SOURCE, TARGET],
)

# Plot: hierarchical layout, each module sits one layer below its deepest dependent
layer = dict.fromkeys(nodes[LABEL], 0)
for _ in range(len(nodes)):
    for src, tgt in zip(df[SOURCE], df[TARGET], strict=True):
        layer[tgt] = max(layer[tgt], layer[src] + 1)
nodes["layer"] = nodes[LABEL].map(layer)
n_layers = nodes["layer"].max() + 1
nodes["slot"] = nodes.groupby("layer").cumcount()
width = nodes.groupby("layer")["slot"].transform("size")
nodes["x"] = (nodes["slot"] + 1) / (width + 1)
nodes["y"] = 1 - nodes["layer"] / max(n_layers - 1, 1)
pos = nodes.set_index(LABEL)[["x", "y"]]

# Shorten edges in screen proportions so arrow tips land on the target node border
PX_PER_X, PX_PER_Y = 560.0, 300.0  # approximate panel pixels per data unit
NODE_RADIUS = 12.0  # node marker radius in the same pixels
p0 = pos.loc[df[SOURCE]].to_numpy() * [PX_PER_X, PX_PER_Y]
p1 = pos.loc[df[TARGET]].to_numpy() * [PX_PER_X, PX_PER_Y]
unit = (p1 - p0) / np.linalg.norm(p1 - p0, axis=1, keepdims=True)
start = (p0 + unit * NODE_RADIUS) / [PX_PER_X, PX_PER_Y]
end = (p1 - unit * (NODE_RADIUS)) / [PX_PER_X, PX_PER_Y]
segments = pd.DataFrame({"x": start[:, 0], "y": start[:, 1], "xend": end[:, 0], "yend": end[:, 1]})

title = "network-directed · python · letsplot · anyplot.ai"
plot = (
    ggplot()
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=segments,
        color=INK_SOFT,
        size=0.6,
        arrow=arrow(length=7, angle=18, type="closed"),
        alpha=0.65,
    )
    + geom_point(aes(x="x", y="y", fill=GROUP), data=nodes, size=11, shape=21, stroke=1.2, color=PAGE_BG)
    + geom_label(
        aes(x="x", y="y", label=LABEL),
        data=nodes,
        size=5.5,
        color=INK,
        fill=PAGE_BG,
        alpha=0.9,
        label_size=0,
        fontface="bold",
        nudge_y=-0.075,
    )
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=16, face="bold", hjust=0.5, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=11, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_position="right",
        plot_margin=[20, 30, 20, 30],
    )
    + labs(title=title)
    + ggsize(800, 450)
    + xlim(nodes["x"].min() - 0.12, nodes["x"].max() + 0.12)
    + ylim(nodes["y"].min() - 0.15, nodes["y"].max() + 0.08)
)

ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
