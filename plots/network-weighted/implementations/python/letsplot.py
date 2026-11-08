""" anyplot.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()
np.random.seed(42)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint position 1: a single node series

# Constants
EDGE_WIDTH = (0.6, 5.0)  # line size of the lightest and the heaviest edge
EDGE_ALPHA = 0.55  # translucent edges keep crossings readable
NODE_SIZE = (7.0, 15.0)  # point size of the node with the least and the most total trade

# Create trade network: 15 countries with weighted trade relationships
countries = [
    "USA",
    "China",
    "Germany",
    "Japan",
    "UK",
    "France",
    "Canada",
    "Mexico",
    "Brazil",
    "India",
    "S.Korea",
    "Italy",
    "Australia",
    "Spain",
    "Netherlands",
]
n_nodes = len(countries)

# Generate edges with weights (bilateral trade in billions USD)
edges_data = []
edge_pairs = [
    (0, 1, 550),
    (0, 2, 180),
    (0, 3, 220),
    (0, 4, 140),
    (0, 6, 380),
    (0, 7, 420),
    (0, 9, 95),
    (0, 10, 130),
    (1, 2, 200),
    (1, 3, 340),
    (1, 4, 85),
    (1, 10, 290),
    (1, 12, 160),
    (2, 3, 55),
    (2, 4, 150),
    (2, 5, 180),
    (2, 8, 45),
    (2, 13, 65),
    (2, 14, 220),
    (3, 4, 35),
    (3, 10, 85),
    (3, 12, 70),
    (4, 5, 95),
    (4, 11, 55),
    (4, 14, 80),
    (5, 11, 85),
    (5, 13, 95),
    (6, 7, 75),
    (7, 8, 40),
    (8, 9, 30),
    (9, 12, 25),
    (11, 13, 45),
    (12, 14, 35),
]

for src, tgt, weight in edge_pairs:
    edges_data.append({"source": src, "target": tgt, "weight": weight})

# Calculate positions using spring layout (simple force-directed simulation)
pos = np.zeros((n_nodes, 2))
# Initial positions in a circle
angles = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)
pos[:, 0] = np.cos(angles)
pos[:, 1] = np.sin(angles)

# Force-directed iterations with weight-aware attraction
for _ in range(150):
    forces = np.zeros_like(pos)

    # Repulsion between all nodes
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            diff = pos[i] - pos[j]
            dist = max(np.linalg.norm(diff), 0.1)
            force = diff / (dist**2) * 0.5
            forces[i] += force
            forces[j] -= force

    # Attraction along edges (weighted)
    for edge in edges_data:
        i, j = edge["source"], edge["target"]
        diff = pos[j] - pos[i]
        dist = max(np.linalg.norm(diff), 0.01)
        # Weight influences attraction strength more strongly
        weight_factor = (np.log1p(edge["weight"]) ** 1.2) * 0.002
        force = diff / dist * weight_factor
        forces[i] += force
        forces[j] -= force

    # Apply forces with damping
    pos += forces * 0.08

    # Center
    pos -= pos.mean(axis=0)

# Scale positions with margin for labels
pos = pos / np.abs(pos).max() * 3.2

# Calculate weighted degree for node sizing
weighted_degree = np.zeros(n_nodes)
for edge in edges_data:
    weighted_degree[edge["source"]] += edge["weight"]
    weighted_degree[edge["target"]] += edge["weight"]

# Create node dataframe
nodes_df = pd.DataFrame({"x": pos[:, 0], "y": pos[:, 1], "label": countries, "weighted_degree": weighted_degree})

# Create edges dataframe with line segments
edges_list = []
for edge in edges_data:
    src, tgt = edge["source"], edge["target"]
    edges_list.append(
        {"x": pos[src, 0], "y": pos[src, 1], "xend": pos[tgt, 0], "yend": pos[tgt, 1], "weight": edge["weight"]}
    )

edges_df = pd.DataFrame(edges_list)

# Edge and node sizes are computed here and drawn through an identity size scale: lets-plot
# has one size scale per plot, and a shared scale trained on the edge weights would shrink
# every node to its minimum. Edge width grows linearly with weight between EDGE_WIDTH bounds.
min_w, max_w = edges_df["weight"].min(), edges_df["weight"].max()
width_per_weight = (EDGE_WIDTH[1] - EDGE_WIDTH[0]) / (max_w - min_w)
edges_df["line_width"] = EDGE_WIDTH[0] + (edges_df["weight"] - min_w) * width_per_weight

# Node diameter grows with the square root of the weighted degree, so its area tracks total trade,
# and the smallest node is still wider than the thickest edge
max_d = nodes_df["weighted_degree"].max()
nodes_df["node_size"] = NODE_SIZE[0] + (NODE_SIZE[1] - NODE_SIZE[0]) * np.sqrt(nodes_df["weighted_degree"] / max_d)

# Legend keys: line widths for round trade volumes inside the data range
legend_weights = [w for w in (100, 200, 300, 400, 500) if min_w <= w <= max_w]
legend_widths = [EDGE_WIDTH[0] + (w - min_w) * width_per_weight for w in legend_weights]

# Edges are translucent, but lets-plot draws line keys opaque: the keys get the color an edge
# shows on the page
ink_rgb, page_rgb = (np.array([int(h[i : i + 2], 16) for i in (1, 3, 5)]) for h in (INK_SOFT, PAGE_BG))
edge_key_color = "#" + "".join(f"{round(c):02X}" for c in EDGE_ALPHA * ink_rgb + (1 - EDGE_ALPHA) * page_rgb)

# Frame the layout with room for the labels above the nodes
x_lim = [nodes_df["x"].min() - 0.6, nodes_df["x"].max() + 0.6]
y_lim = [nodes_df["y"].min() - 0.4, nodes_df["y"].max() + 1.0]

# Create the plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_blank(),
    panel_grid=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(size=16, face="bold", color=INK),
    plot_subtitle=element_text(size=11, color=INK_SOFT),
    plot_caption=element_text(size=10, color=INK_SOFT),
    legend_title=element_text(size=11, color=INK),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_background=element_blank(),
    legend_position="right",
)

plot = (
    ggplot()
    # Edges as segments, width from trade volume
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend", size="line_width"),
        data=edges_df,
        color=INK_SOFT,
        alpha=EDGE_ALPHA,
        tooltips=layer_tooltips().line("Trade|@weight B USD"),
    )
    # Nodes drawn on top of the edges, sized by weighted degree
    + geom_point(
        aes(x="x", y="y", size="node_size"),
        data=nodes_df,
        shape=21,
        fill=BRAND,
        color=PAGE_BG,
        stroke=1.0,
        show_legend=False,
        tooltips=layer_tooltips().title("@label").line("Total trade|@weighted_degree B USD"),
    )
    # Node labels on a page-colored plate just above the largest node's radius, so no edge runs
    # through a name
    + geom_label(
        aes(x="x", y="y", label="label"),
        data=nodes_df,
        size=6,
        color=INK,
        fill=PAGE_BG,
        fontface="bold",
        label_size=0,
        label_padding=0.15,
        vjust=0,
        nudge_y=NODE_SIZE[1] / 2 + 1,
        nudge_unit="size",
        tooltips="none",
    )
    + scale_size_identity(
        name="Trade volume\n(billion USD)",
        breaks=legend_widths,
        labels=[str(w) for w in legend_weights],
        guide="legend",
    )
    + guides(size=guide_legend(override_aes={"color": edge_key_color}))
    # Styling
    + labs(
        title="network-weighted · python · letsplot · anyplot.ai",
        subtitle="International trade network: edge thickness = bilateral trade volume",
        caption="Node size = each country's total trade with the others shown (weighted degree)",
    )
    + scale_x_continuous(limits=x_lim)
    + scale_y_continuous(limits=y_lim)
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save PNG (scaled 4x for 3200 × 1800 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)

# Save HTML for interactive version
ggsave(plot, f"plot-{THEME}.html", path=".")
