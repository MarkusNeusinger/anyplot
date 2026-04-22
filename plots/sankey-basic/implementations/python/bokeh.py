""" pyplots.ai
sankey-basic: Basic Sankey Diagram
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Label
from bokeh.plotting import figure


# Data - Energy flow from sources to sectors (TWh)
flows = [
    {"source": "Coal", "target": "Industrial", "value": 25},
    {"source": "Coal", "target": "Residential", "value": 10},
    {"source": "Gas", "target": "Residential", "value": 30},
    {"source": "Gas", "target": "Commercial", "value": 20},
    {"source": "Gas", "target": "Industrial", "value": 15},
    {"source": "Nuclear", "target": "Industrial", "value": 18},
    {"source": "Nuclear", "target": "Commercial", "value": 12},
    {"source": "Hydro", "target": "Residential", "value": 8},
    {"source": "Hydro", "target": "Commercial", "value": 7},
    {"source": "Solar", "target": "Residential", "value": 5},
    {"source": "Solar", "target": "Commercial", "value": 6},
]

# Extract unique sources and targets (preserve order)
sources = []
targets = []
for f in flows:
    if f["source"] not in sources:
        sources.append(f["source"])
    if f["target"] not in targets:
        targets.append(f["target"])

# Color palette for sources (Python Blue first, then colorblind-safe)
source_colors = {
    "Coal": "#306998",  # Python Blue
    "Gas": "#FFD43B",  # Python Yellow
    "Nuclear": "#9B59B6",  # Purple
    "Hydro": "#3498DB",  # Light blue
    "Solar": "#E67E22",  # Orange
}

# Target colors (darker shades)
target_colors = {
    "Industrial": "#2C3E50",  # Dark blue-grey
    "Commercial": "#1ABC9C",  # Teal
    "Residential": "#E74C3C",  # Red
}

# Calculate totals for node sizing
source_totals = {s: sum(f["value"] for f in flows if f["source"] == s) for s in sources}
target_totals = {t: sum(f["value"] for f in flows if f["target"] == t) for t in targets}

# Layout parameters
left_x = 0
right_x = 100
node_width = 8
node_gap = 3
total_height = 100
padding_y = 5

# Calculate node positions for sources (left side)
source_height_total = sum(source_totals.values())
scale_factor = (total_height - 2 * padding_y - (len(sources) - 1) * node_gap) / source_height_total

source_nodes = {}
current_y = padding_y
for s in sources:
    height = source_totals[s] * scale_factor
    source_nodes[s] = {"x": left_x, "y": current_y, "height": height, "value": source_totals[s]}
    current_y += height + node_gap

# Calculate node positions for targets (right side)
target_height_total = sum(target_totals.values())
scale_factor_t = (total_height - 2 * padding_y - (len(targets) - 1) * node_gap) / target_height_total

target_nodes = {}
current_y = padding_y
for t in targets:
    height = target_totals[t] * scale_factor_t
    target_nodes[t] = {"x": right_x - node_width, "y": current_y, "height": height, "value": target_totals[t]}
    current_y += height + node_gap

# Track flow offsets for stacking flows at each node
source_offsets = dict.fromkeys(sources, 0)
target_offsets = dict.fromkeys(targets, 0)

# Create figure (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="Energy Flow · sankey-basic · bokeh · pyplots.ai",
    x_range=(-15, 115),
    y_range=(-5, 105),
    tools="",
    toolbar_location=None,
)

# Draw flows using bezier curves
for f in flows:
    src = f["source"]
    tgt = f["target"]
    value = f["value"]

    # Get node info
    src_node = source_nodes[src]
    tgt_node = target_nodes[tgt]

    # Flow height proportional to value
    src_flow_height = (value / source_totals[src]) * src_node["height"]
    tgt_flow_height = (value / target_totals[tgt]) * tgt_node["height"]

    # Source connection points
    x0 = src_node["x"] + node_width
    y0_bottom = src_node["y"] + source_offsets[src]
    y0_top = y0_bottom + src_flow_height

    # Target connection points
    x1 = tgt_node["x"]
    y1_bottom = tgt_node["y"] + target_offsets[tgt]
    y1_top = y1_bottom + tgt_flow_height

    # Update offsets for stacking
    source_offsets[src] += src_flow_height
    target_offsets[tgt] += tgt_flow_height

    # Create smooth bezier flow path
    t = np.linspace(0, 1, 50)
    cx0 = x0 + (x1 - x0) * 0.4
    cx1 = x0 + (x1 - x0) * 0.6

    # Cubic bezier for x positions
    x_path = (1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * cx0 + 3 * (1 - t) * t**2 * cx1 + t**3 * x1

    # Linear interpolation for y positions
    y_bottom = (1 - t) * y0_bottom + t * y1_bottom
    y_top = (1 - t) * y0_top + t * y1_top

    # Create closed polygon
    xs = list(x_path) + list(x_path[::-1])
    ys = list(y_top) + list(y_bottom[::-1])

    # Draw flow with source color and transparency
    p.patch(
        xs,
        ys,
        fill_color=source_colors[src],
        fill_alpha=0.5,
        line_color=source_colors[src],
        line_alpha=0.7,
        line_width=1,
    )

# Draw source nodes (left side)
for s in sources:
    node = source_nodes[s]
    p.quad(
        left=node["x"],
        right=node["x"] + node_width,
        bottom=node["y"],
        top=node["y"] + node["height"],
        fill_color=source_colors[s],
        fill_alpha=0.9,
        line_color="white",
        line_width=2,
    )
    # Add label to the left of node
    label = Label(
        x=node["x"] - 1,
        y=node["y"] + node["height"] / 2,
        text=f"{s} ({node['value']} TWh)",
        text_font_size="22pt",
        text_align="right",
        text_baseline="middle",
        text_color="#333333",
    )
    p.add_layout(label)

# Draw target nodes (right side)
for t in targets:
    node = target_nodes[t]
    p.quad(
        left=node["x"],
        right=node["x"] + node_width,
        bottom=node["y"],
        top=node["y"] + node["height"],
        fill_color=target_colors[t],
        fill_alpha=0.9,
        line_color="white",
        line_width=2,
    )
    # Add label to the right of node
    label = Label(
        x=node["x"] + node_width + 1,
        y=node["y"] + node["height"] / 2,
        text=f"{t} ({node['value']} TWh)",
        text_font_size="22pt",
        text_align="left",
        text_baseline="middle",
        text_color="#333333",
    )
    p.add_layout(label)

# Styling
p.title.text_font_size = "32pt"
p.title.align = "center"

# Hide axes for cleaner Sankey look
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Background
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FFFFFF"

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html")
