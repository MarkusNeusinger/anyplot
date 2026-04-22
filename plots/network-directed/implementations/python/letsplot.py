""" pyplots.ai
network-directed: Directed Network Graph
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    arrow,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
    xlim,
    ylim,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

np.random.seed(42)

# Define software package dependency network
nodes = [
    {"id": "app", "label": "App", "group": "application"},
    {"id": "api", "label": "API", "group": "core"},
    {"id": "auth", "label": "Auth", "group": "core"},
    {"id": "db", "label": "Database", "group": "core"},
    {"id": "cache", "label": "Cache", "group": "infrastructure"},
    {"id": "config", "label": "Config", "group": "utility"},
    {"id": "logger", "label": "Logger", "group": "utility"},
    {"id": "utils", "label": "Utils", "group": "utility"},
    {"id": "http", "label": "HTTP Client", "group": "infrastructure"},
    {"id": "queue", "label": "Queue", "group": "infrastructure"},
]

# Directed edges (source depends on target, arrow from source to target)
edges = [
    ("app", "api"),
    ("app", "config"),
    ("api", "auth"),
    ("api", "db"),
    ("api", "cache"),
    ("api", "logger"),
    ("auth", "db"),
    ("auth", "config"),
    ("auth", "logger"),
    ("db", "config"),
    ("db", "logger"),
    ("cache", "config"),
    ("cache", "logger"),
    ("http", "config"),
    ("http", "logger"),
    ("queue", "config"),
    ("queue", "logger"),
    ("api", "http"),
    ("api", "queue"),
    ("utils", "logger"),
]

# Create node positions using a hierarchical-like layout
# Manually place nodes in layers for clear dependency visualization
node_positions = {
    "app": (0.5, 1.0),
    "api": (0.5, 0.75),
    "auth": (0.15, 0.5),
    "db": (0.5, 0.5),
    "cache": (0.85, 0.5),
    "http": (0.05, 0.25),
    "queue": (0.3, 0.25),
    "config": (0.55, 0.25),
    "logger": (0.8, 0.25),
    "utils": (1.0, 0.75),
}

# Build node dataframe
node_df = pd.DataFrame(nodes)
node_df["x"] = node_df["id"].map(lambda n: node_positions[n][0])
node_df["y"] = node_df["id"].map(lambda n: node_positions[n][1])

# Color mapping for groups
group_colors = {
    "application": "#306998",  # Python Blue
    "core": "#FFD43B",  # Python Yellow
    "infrastructure": "#22C55E",  # Green
    "utility": "#A855F7",  # Purple
}
node_df["color"] = node_df["group"].map(group_colors)

# Build edge dataframe with arrow endpoints
edge_data = []
for source, target in edges:
    x0, y0 = node_positions[source]
    x1, y1 = node_positions[target]

    # Shorten edges to not overlap with nodes
    dx, dy = x1 - x0, y1 - y0
    length = np.sqrt(dx**2 + dy**2)
    if length > 0:
        # Shrink by node radius on each end
        shrink = 0.05
        x0_adj = x0 + (dx / length) * shrink
        y0_adj = y0 + (dy / length) * shrink
        x1_adj = x1 - (dx / length) * shrink * 1.8  # More shrink for arrow head
        y1_adj = y1 - (dy / length) * shrink * 1.8
    else:
        x0_adj, y0_adj, x1_adj, y1_adj = x0, y0, x1, y1

    edge_data.append({"x": x0_adj, "y": y0_adj, "xend": x1_adj, "yend": y1_adj})

edge_df = pd.DataFrame(edge_data)

# Create the plot
plot = (
    ggplot()
    # Draw edges with arrows
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=edge_df,
        color="#64748B",
        size=1.2,
        arrow=arrow(length=12, type="closed"),
        alpha=0.7,
    )
    # Draw nodes
    + geom_point(aes(x="x", y="y", fill="group"), data=node_df, size=22, shape=21, stroke=2.5, color="white")
    # Add node labels below nodes
    + geom_text(
        aes(x="x", y="y", label="label"), data=node_df, size=12, color="#1E293B", fontface="bold", nudge_y=-0.06
    )
    # Color scale
    + scale_fill_manual(values=["#306998", "#FFD43B", "#22C55E", "#A855F7"], name="Module Type")
    # Theme and styling
    + theme_void()
    + theme(
        plot_title=element_text(size=28, face="bold", hjust=0.5),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        plot_margin=[60, 80, 80, 60],
    )
    + labs(title="network-directed · letsplot · pyplots.ai")
    + ggsize(1600, 900)
    + xlim(-0.05, 1.15)
    + ylim(0.1, 1.1)
)

# Save as PNG and HTML
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")

# Move files from lets-plot-images subdirectory to current directory
if os.path.exists("lets-plot-images/plot.png"):
    shutil.move("lets-plot-images/plot.png", "plot.png")
if os.path.exists("lets-plot-images/plot.html"):
    shutil.move("lets-plot-images/plot.html", "plot.html")
if os.path.exists("lets-plot-images") and not os.listdir("lets-plot-images"):
    os.rmdir("lets-plot-images")
