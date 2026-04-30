""" anyplot.ai
sankey-basic: Basic Sankey Diagram
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-04-30
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_rect,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for source categories (canonical order, first = #009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Energy flow data: sources -> sectors (realistic energy distribution)
flows = [
    ("Coal", "Industrial", 28),
    ("Coal", "Residential", 8),
    ("Natural Gas", "Industrial", 22),
    ("Natural Gas", "Residential", 35),
    ("Natural Gas", "Commercial", 18),
    ("Nuclear", "Industrial", 16),
    ("Nuclear", "Commercial", 12),
    ("Renewable", "Residential", 14),
    ("Renewable", "Commercial", 10),
    ("Renewable", "Industrial", 6),
]

sources = ["Coal", "Natural Gas", "Nuclear", "Renewable"]
targets = ["Industrial", "Residential", "Commercial"]
source_color_map = dict(zip(sources, OKABE_ITO, strict=True))

# Calculate totals for each node
source_totals = {}
for src, _, val in flows:
    source_totals[src] = source_totals.get(src, 0) + val

target_totals = {}
for _, tgt, val in flows:
    target_totals[tgt] = target_totals.get(tgt, 0) + val

# Layout parameters
total_flow = sum(v for _, _, v in flows)
node_gap = 0.04
x_left = 0.18
x_right = 0.82

# Position source nodes (left side)
source_positions = {}
y_offset = 0.05
for src in sources:
    height = source_totals.get(src, 0) / total_flow * 0.85
    source_positions[src] = {"y0": y_offset, "y1": y_offset + height, "x": x_left}
    y_offset += height + node_gap

# Position target nodes (right side)
target_positions = {}
y_offset = 0.05
for tgt in targets:
    height = target_totals.get(tgt, 0) / total_flow * 0.85
    target_positions[tgt] = {"y0": y_offset, "y1": y_offset + height, "x": x_right}
    y_offset += height + node_gap

# Track flow offsets within each node
source_offsets = dict.fromkeys(sources, 0)
target_offsets = dict.fromkeys(targets, 0)

# Build flow polygons with smooth cubic bezier curves
flow_data = []

for src, tgt, val in flows:
    flow_height = val / total_flow * 0.85

    src_y0 = source_positions[src]["y0"] + source_offsets[src]
    src_y1 = src_y0 + flow_height
    source_offsets[src] += flow_height

    tgt_y0 = target_positions[tgt]["y0"] + target_offsets[tgt]
    tgt_y1 = tgt_y0 + flow_height
    target_offsets[tgt] += flow_height

    n_points = 40
    x_vals_top, y_vals_top = [], []
    x_vals_bottom, y_vals_bottom = [], []

    for i in range(n_points + 1):
        t = i / n_points
        x = x_left + t * (x_right - x_left)
        ease = t * t * (3 - 2 * t)
        x_vals_top.append(x)
        y_vals_top.append(src_y1 + ease * (tgt_y1 - src_y1))
        x_vals_bottom.append(x)
        y_vals_bottom.append(src_y0 + ease * (tgt_y0 - src_y0))

    x_polygon = x_vals_top + x_vals_bottom[::-1]
    y_polygon = y_vals_top + y_vals_bottom[::-1]

    for x, y in zip(x_polygon, y_polygon, strict=False):
        flow_data.append({"x": x, "y": y, "flow_id": f"{src}->{tgt}", "source": src, "value": val})

df_flows = pd.DataFrame(flow_data)

# Build node rectangles
node_rects = []
node_width = 0.025

for src in sources:
    pos = source_positions[src]
    node_rects.append(
        {"xmin": pos["x"] - node_width / 2, "xmax": pos["x"] + node_width / 2, "ymin": pos["y0"], "ymax": pos["y1"]}
    )

for tgt in targets:
    pos = target_positions[tgt]
    node_rects.append(
        {"xmin": pos["x"] - node_width / 2, "xmax": pos["x"] + node_width / 2, "ymin": pos["y0"], "ymax": pos["y1"]}
    )

df_nodes = pd.DataFrame(node_rects)

# Build labels with flow totals
labels = []
for src in sources:
    pos = source_positions[src]
    labels.append(
        {
            "x": pos["x"] - node_width - 0.015,
            "y": (pos["y0"] + pos["y1"]) / 2,
            "label": f"{src}\n({source_totals[src]} TWh)",
            "side": "left",
        }
    )

for tgt in targets:
    pos = target_positions[tgt]
    labels.append(
        {
            "x": pos["x"] + node_width + 0.015,
            "y": (pos["y0"] + pos["y1"]) / 2,
            "label": f"{tgt}\n({target_totals[tgt]} TWh)",
            "side": "right",
        }
    )

df_labels = pd.DataFrame(labels)

# Plot
plot = (
    ggplot()
    + geom_polygon(
        aes(x="x", y="y", group="flow_id", fill="source"), data=df_flows, alpha=0.65, color=PAGE_BG, size=0.2
    )
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), data=df_nodes, fill=INK, color=INK, size=1.5)
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_labels[df_labels["side"] == "left"],
        size=14,
        hjust=1,
        color=INK_SOFT,
        family="sans-serif",
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_labels[df_labels["side"] == "right"],
        size=14,
        hjust=0,
        color=INK_SOFT,
        family="sans-serif",
    )
    + scale_fill_manual(values=[source_color_map[s] for s in sources], name="Energy Source")
    + labs(title="Energy Flow · sankey-basic · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=30, face="bold", color=INK),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_text=element_text(size=18, color=INK_SOFT),
        legend_title=element_text(size=20, face="bold", color=INK),
        legend_position="bottom",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
    + scale_x_continuous(limits=[-0.02, 1.02])
    + scale_y_continuous(limits=[-0.02, 1.02])
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800 × 2700 px) and HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
