"""anyplot.ai
sankey-basic: Basic Sankey Diagram
Library: plotnine 0.15.3 | Python 3.13.13
Quality: 76/100 | Updated: 2026-04-30
"""

import os
import sys


sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.dirname(os.path.abspath(__file__))]

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Energy flow from sources to sectors
flows = pd.DataFrame(
    {
        "source": ["Coal", "Coal", "Gas", "Gas", "Gas", "Nuclear", "Nuclear", "Renewables", "Renewables"],
        "target": [
            "Industrial",
            "Residential",
            "Industrial",
            "Commercial",
            "Residential",
            "Commercial",
            "Residential",
            "Commercial",
            "Residential",
        ],
        "value": [35, 15, 25, 20, 15, 18, 12, 8, 12],
    }
)

# Define node positions
sources = ["Coal", "Gas", "Nuclear", "Renewables"]
targets = ["Industrial", "Commercial", "Residential"]

# X positions with margins for labels
x_left = 0.2
x_right = 0.8
node_width = 0.08
node_gap = 0.03

# Calculate node sizes based on total flow
source_totals = flows.groupby("source")["value"].sum().to_dict()
target_totals = flows.groupby("target")["value"].sum().to_dict()
total_flow = flows["value"].sum()

# Calculate source node positions (left side)
source_positions = {}
current_y = 1.0
for src in sources:
    height = source_totals[src] / total_flow * 0.8
    source_positions[src] = {
        "x": x_left,
        "y_top": current_y,
        "y_bottom": current_y - height,
        "height": height,
        "flow_offset": 0,
    }
    current_y = current_y - height - node_gap

# Calculate target node positions (right side)
target_positions = {}
current_y = 1.0
for tgt in targets:
    height = target_totals[tgt] / total_flow * 0.8
    target_positions[tgt] = {
        "x": x_right,
        "y_top": current_y,
        "y_bottom": current_y - height,
        "height": height,
        "flow_offset": 0,
    }
    current_y = current_y - height - node_gap

# Okabe-Ito colors for sources; theme-adaptive neutral for targets
source_colors_map = {"Coal": OKABE_ITO[0], "Gas": OKABE_ITO[1], "Nuclear": OKABE_ITO[2], "Renewables": OKABE_ITO[3]}
target_colors_map = {"Industrial": INK_SOFT, "Commercial": INK_SOFT, "Residential": INK_SOFT}

# Build node rectangles dataframe
node_data = []
for src in sources:
    pos = source_positions[src]
    node_data.append(
        {
            "name": src,
            "xmin": pos["x"],
            "xmax": pos["x"] + node_width,
            "ymin": pos["y_bottom"],
            "ymax": pos["y_top"],
            "label_x": pos["x"] - 0.02,
            "label_y": (pos["y_top"] + pos["y_bottom"]) / 2,
            "side": "source",
            "node_color": src,
        }
    )

for tgt in targets:
    pos = target_positions[tgt]
    node_data.append(
        {
            "name": tgt,
            "xmin": pos["x"] - node_width,
            "xmax": pos["x"],
            "ymin": pos["y_bottom"],
            "ymax": pos["y_top"],
            "label_x": pos["x"] + 0.02,
            "label_y": (pos["y_top"] + pos["y_bottom"]) / 2,
            "side": "target",
            "node_color": tgt,
        }
    )

nodes_df = pd.DataFrame(node_data)

# Build flow polygons (curved paths between nodes)
flow_polygons = []
flow_labels = []
for _, row in flows.iterrows():
    src = row["source"]
    tgt = row["target"]
    val = row["value"]

    flow_height = val / total_flow * 0.8

    src_pos = source_positions[src]
    src_y_top = src_pos["y_top"] - src_pos["flow_offset"]
    src_y_bottom = src_y_top - flow_height
    src_pos["flow_offset"] += flow_height

    tgt_pos = target_positions[tgt]
    tgt_y_top = tgt_pos["y_top"] - tgt_pos["flow_offset"]
    tgt_y_bottom = tgt_y_top - flow_height
    tgt_pos["flow_offset"] += flow_height

    # Smooth cubic Hermite interpolation for flow curves
    flow_x_left = x_left + node_width
    flow_x_right = x_right - node_width
    n_points = 50

    t = np.linspace(0, 1, n_points)
    x_top = flow_x_left + (flow_x_right - flow_x_left) * t
    y_top = src_y_top + (tgt_y_top - src_y_top) * (3 * t**2 - 2 * t**3)

    x_bottom = flow_x_right + (flow_x_left - flow_x_right) * t
    y_bottom = tgt_y_bottom + (src_y_bottom - tgt_y_bottom) * (3 * t**2 - 2 * t**3)

    x_polygon = np.concatenate([x_top, x_bottom])
    y_polygon = np.concatenate([y_top, y_bottom])

    for i in range(len(x_polygon)):
        flow_polygons.append({"x": x_polygon[i], "y": y_polygon[i], "flow_id": f"{src}_{tgt}", "source": src})

    mid_idx = n_points // 2
    flow_center_y = (y_top[mid_idx] + y_bottom[n_points - 1 - mid_idx]) / 2
    src_idx = sources.index(src)
    label_x_offset = 0.35 + src_idx * 0.1
    flow_labels.append({"x": label_x_offset, "y": flow_center_y, "value": str(val), "flow_height": flow_height})

flows_df = pd.DataFrame(flow_polygons)
flow_labels_df = pd.DataFrame(flow_labels)

# Create the plot
plot = (
    ggplot()
    # Flow polygons with transparency
    + geom_polygon(flows_df, aes(x="x", y="y", group="flow_id", fill="source"), alpha=0.5)
    # Node rectangles
    + geom_rect(
        nodes_df, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="node_color"), color="white", size=0.5
    )
    # Flow value labels (only for larger flows to avoid clutter)
    + geom_text(
        flow_labels_df[flow_labels_df["flow_height"] >= 0.05],
        aes(x="x", y="y", label="value"),
        ha="center",
        va="center",
        size=11,
        color=INK,
        fontweight="bold",
    )
    # Source labels (right-aligned)
    + geom_text(
        nodes_df[nodes_df["side"] == "source"],
        aes(x="label_x", y="label_y", label="name"),
        ha="right",
        size=16,
        color=INK,
        fontweight="bold",
    )
    # Target labels (left-aligned)
    + geom_text(
        nodes_df[nodes_df["side"] == "target"],
        aes(x="label_x", y="label_y", label="name"),
        ha="left",
        size=16,
        color=INK,
        fontweight="bold",
    )
    + scale_fill_manual(values={**source_colors_map, **target_colors_map})
    + labs(title="Energy Flow · sankey-basic · plotnine · anyplot.ai", x="", y="")
    + coord_cartesian(xlim=(-0.05, 1.1))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=24, ha="center", weight="bold", color=INK),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_position="none",
    )
    + annotate("text", x=x_left + node_width / 2, y=-0.05, label="Sources", size=16, color=INK_SOFT, fontweight="bold")
    + annotate("text", x=x_right - node_width / 2, y=-0.05, label="Sectors", size=16, color=INK_SOFT, fontweight="bold")
)

plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
