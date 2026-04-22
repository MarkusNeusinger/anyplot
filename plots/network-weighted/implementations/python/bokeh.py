""" pyplots.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-08
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, Range1d
from bokeh.plotting import figure


# Data: Trade network between 15 countries (billions USD annual trade volume)
np.random.seed(42)

# Define nodes (15 countries/regions)
node_labels = [
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
    "S. Korea",
    "Australia",
    "Singapore",
    "Netherlands",
    "Switzerland",
]
n_nodes = len(node_labels)

# Generate weighted edges (trade relationships)
# Not all pairs are connected - create a realistic trade network
edges = [
    # USA trade partners
    (0, 1, 580),  # USA-China
    (0, 2, 180),  # USA-Germany
    (0, 3, 220),  # USA-Japan
    (0, 4, 130),  # USA-UK
    (0, 6, 620),  # USA-Canada
    (0, 7, 680),  # USA-Mexico
    (0, 10, 170),  # USA-S.Korea
    # China trade partners
    (1, 3, 340),  # China-Japan
    (1, 10, 290),  # China-S.Korea
    (1, 2, 220),  # China-Germany
    (1, 11, 180),  # China-Australia
    (1, 12, 120),  # China-Singapore
    (1, 9, 110),  # China-India
    # European connections
    (2, 4, 160),  # Germany-UK
    (2, 5, 180),  # Germany-France
    (2, 13, 200),  # Germany-Netherlands
    (2, 14, 140),  # Germany-Switzerland
    (4, 5, 110),  # UK-France
    (5, 13, 90),  # France-Netherlands
    # Asian connections
    (3, 10, 85),  # Japan-S.Korea
    (9, 12, 55),  # India-Singapore
    (12, 11, 70),  # Singapore-Australia
    # Americas
    (6, 7, 80),  # Canada-Mexico
    (0, 8, 95),  # USA-Brazil
    (8, 9, 40),  # Brazil-India
]

# Use spring layout (force-directed) for node positions
# Compute initial positions using a simple force-directed approach
positions = np.random.rand(n_nodes, 2) * 10

# Simple force-directed layout
for _ in range(100):
    forces = np.zeros((n_nodes, 2))

    # Repulsion between all nodes
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            diff = positions[i] - positions[j]
            dist = np.linalg.norm(diff) + 0.1
            force = diff / (dist**2) * 2
            forces[i] += force
            forces[j] -= force

    # Attraction along edges (weighted)
    for src, tgt, weight in edges:
        diff = positions[tgt] - positions[src]
        dist = np.linalg.norm(diff) + 0.1
        force = diff * 0.01 * (weight / 200)
        forces[src] += force
        forces[tgt] -= force

    positions += forces * 0.1

# Center and scale positions
positions -= positions.mean(axis=0)
positions /= positions.max() * 1.2

node_x = positions[:, 0]
node_y = positions[:, 1]

# Calculate weighted degree for node sizing
weighted_degree = np.zeros(n_nodes)
for src, tgt, weight in edges:
    weighted_degree[src] += weight
    weighted_degree[tgt] += weight

# Normalize node sizes
min_size = 30
max_size = 80
node_sizes = min_size + (weighted_degree - weighted_degree.min()) / (
    weighted_degree.max() - weighted_degree.min() + 0.1
) * (max_size - min_size)

# Prepare edge data
edge_x0, edge_y0, edge_x1, edge_y1 = [], [], [], []
edge_widths = []
edge_colors = []

# Normalize edge weights to line widths
max_weight = max(e[2] for e in edges)
min_weight = min(e[2] for e in edges)

for src, tgt, weight in edges:
    edge_x0.append(node_x[src])
    edge_y0.append(node_y[src])
    edge_x1.append(node_x[tgt])
    edge_y1.append(node_y[tgt])

    # Scale width: thinnest = 2, thickest = 20
    normalized = (weight - min_weight) / (max_weight - min_weight + 0.1)
    edge_widths.append(2 + normalized * 18)

    # Color by weight (darker = stronger)
    alpha = 0.3 + normalized * 0.5
    edge_colors.append(f"rgba(48, 105, 152, {alpha})")

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="network-weighted · bokeh · pyplots.ai",
    x_axis_label="",
    y_axis_label="",
    tools="",
    toolbar_location=None,
)

# Remove axes and grid (network graphs don't need them)
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Set title style
p.title.text_font_size = "32pt"
p.title.align = "center"

# Set range with padding
padding = 0.15
p.x_range = Range1d(node_x.min() - padding, node_x.max() + padding)
p.y_range = Range1d(node_y.min() - padding, node_y.max() + padding)

# Draw edges (as individual segments with varying widths)
for i in range(len(edge_x0)):
    p.segment(
        x0=[edge_x0[i]],
        y0=[edge_y0[i]],
        x1=[edge_x1[i]],
        y1=[edge_y1[i]],
        line_width=edge_widths[i],
        line_color="#306998",
        line_alpha=0.3 + (edge_widths[i] - 2) / 18 * 0.5,
        line_cap="round",
    )

# Create node source with weighted degree for hover
node_source = ColumnDataSource(
    data={
        "x": node_x,
        "y": node_y,
        "size": node_sizes,
        "labels": node_labels,
        "weighted_degree": [f"{int(wd):,}" for wd in weighted_degree],
    }
)

# Draw nodes
nodes_renderer = p.scatter(
    x="x",
    y="y",
    source=node_source,
    size="size",
    fill_color="#FFD43B",
    line_color="#306998",
    line_width=3,
    fill_alpha=0.9,
)

# Add hover tool for interactivity
hover = HoverTool(
    renderers=[nodes_renderer], tooltips=[("Country", "@labels"), ("Total Trade (B USD)", "@weighted_degree")]
)
p.add_tools(hover)

# Add node labels
labels = LabelSet(
    x="x",
    y="y",
    text="labels",
    source=node_source,
    text_font_size="16pt",
    text_align="center",
    text_baseline="middle",
    text_color="#1a1a1a",
    text_font_style="bold",
)
p.add_layout(labels)

# Add legend annotation for edge thickness
# Create a prominent manual legend in the corner
legend_x = node_x.min() - padding + 0.03
legend_y = node_y.max() + padding - 0.02

# Legend title
p.text(
    x=[legend_x],
    y=[legend_y],
    text=["Trade Volume (B USD)"],
    text_font_size="22pt",
    text_font_style="bold",
    text_color="#1a1a1a",
)

# Legend lines showing weight scale - made more prominent
legend_weights = [min_weight, (min_weight + max_weight) / 2, max_weight]
legend_labels = [f"{int(w)} B" for w in legend_weights]
legend_widths = [4, 14, 26]  # Increased widths for visibility

for i, (lw, label) in enumerate(zip(legend_widths, legend_labels, strict=True)):
    y_pos = legend_y - 0.055 - i * 0.05
    # Longer legend lines for better visibility
    p.segment(
        x0=[legend_x],
        y0=[y_pos],
        x1=[legend_x + 0.12],
        y1=[y_pos],
        line_width=lw,
        line_color="#306998",
        line_alpha=0.6 + i * 0.15,
        line_cap="round",
    )
    p.text(
        x=[legend_x + 0.14],
        y=[y_pos],
        text=[label],
        text_font_size="18pt",
        text_baseline="middle",
        text_color="#1a1a1a",
    )

# Export to PNG and HTML (for interactivity)
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="network-weighted · bokeh · pyplots.ai")
