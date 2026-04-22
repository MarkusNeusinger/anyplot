""" pyplots.ai
sankey-basic: Basic Sankey Diagram
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
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

# Define node ordering
sources = ["Coal", "Natural Gas", "Nuclear", "Renewable"]
targets = ["Industrial", "Residential", "Commercial"]

# Calculate totals for each node
source_totals = {}
for src, _, val in flows:
    source_totals[src] = source_totals.get(src, 0) + val

target_totals = {}
for _, tgt, val in flows:
    target_totals[tgt] = target_totals.get(tgt, 0) + val

# Normalize positions
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

# Build flow polygons with smooth bezier curves
flow_data = []

for src, tgt, val in flows:
    flow_height = val / total_flow * 0.85

    # Source connection points
    src_y0 = source_positions[src]["y0"] + source_offsets[src]
    src_y1 = src_y0 + flow_height
    source_offsets[src] += flow_height

    # Target connection points
    tgt_y0 = target_positions[tgt]["y0"] + target_offsets[tgt]
    tgt_y1 = tgt_y0 + flow_height
    target_offsets[tgt] += flow_height

    # Create smooth bezier polygon for flow
    n_points = 40
    x_vals_top = []
    y_vals_top = []
    x_vals_bottom = []
    y_vals_bottom = []

    for i in range(n_points + 1):
        t = i / n_points
        x = x_left + t * (x_right - x_left)
        # Smooth cubic bezier easing
        ease = t * t * (3 - 2 * t)
        y_top = src_y1 + ease * (tgt_y1 - src_y1)
        y_bottom = src_y0 + ease * (tgt_y0 - src_y0)

        x_vals_top.append(x)
        y_vals_top.append(y_top)
        x_vals_bottom.append(x)
        y_vals_bottom.append(y_bottom)

    # Combine into closed polygon
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
        {
            "xmin": pos["x"] - node_width / 2,
            "xmax": pos["x"] + node_width / 2,
            "ymin": pos["y0"],
            "ymax": pos["y1"],
            "label": src,
            "side": "source",
        }
    )

for tgt in targets:
    pos = target_positions[tgt]
    node_rects.append(
        {
            "xmin": pos["x"] - node_width / 2,
            "xmax": pos["x"] + node_width / 2,
            "ymin": pos["y0"],
            "ymax": pos["y1"],
            "label": tgt,
            "side": "target",
        }
    )

df_nodes = pd.DataFrame(node_rects)

# Build labels with flow values
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

# Colors for each energy source
source_colors = {"Coal": "#4A4A4A", "Natural Gas": "#306998", "Nuclear": "#9B59B6", "Renewable": "#27AE60"}

# Create the plot
plot = (
    ggplot()
    + geom_polygon(
        aes(x="x", y="y", group="flow_id", fill="source"), data=df_flows, alpha=0.65, color="white", size=0.2
    )
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=df_nodes,
        fill="#2C3E50",
        color="#1A252F",
        size=1.5,
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_labels[df_labels["side"] == "left"],
        size=14,
        hjust=1,
        family="sans-serif",
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_labels[df_labels["side"] == "right"],
        size=14,
        hjust=0,
        family="sans-serif",
    )
    + scale_fill_manual(values=[source_colors[s] for s in sources], name="Energy Source")
    + labs(title="Energy Flow · sankey-basic · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=30, face="bold"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_text=element_text(size=18),
        legend_title=element_text(size=20, face="bold"),
        legend_position="bottom",
    )
    + scale_x_continuous(limits=[-0.02, 1.02])
    + scale_y_continuous(limits=[-0.02, 1.02])
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
