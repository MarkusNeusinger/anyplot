""" pyplots.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-09
"""

import re

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Set seed for reproducibility
np.random.seed(42)

# Data: Trade network between countries (billions USD)
nodes = {
    "USA": {"group": "Americas"},
    "CAN": {"group": "Americas"},
    "MEX": {"group": "Americas"},
    "BRA": {"group": "Americas"},
    "DEU": {"group": "Europe"},
    "FRA": {"group": "Europe"},
    "GBR": {"group": "Europe"},
    "ITA": {"group": "Europe"},
    "CHN": {"group": "Asia"},
    "JPN": {"group": "Asia"},
    "KOR": {"group": "Asia"},
    "IND": {"group": "Asia"},
    "AUS": {"group": "Oceania"},
}

# Define edges with trade volume weights (billions USD)
edges = [
    ("USA", "CAN", 650),
    ("USA", "MEX", 580),
    ("USA", "CHN", 520),
    ("USA", "JPN", 180),
    ("USA", "DEU", 200),
    ("USA", "GBR", 130),
    ("USA", "KOR", 140),
    ("USA", "BRA", 80),
    ("CAN", "CHN", 75),
    ("CAN", "MEX", 40),
    ("MEX", "CHN", 90),
    ("DEU", "FRA", 170),
    ("DEU", "GBR", 120),
    ("DEU", "ITA", 130),
    ("DEU", "CHN", 200),
    ("FRA", "GBR", 90),
    ("FRA", "ITA", 80),
    ("FRA", "CHN", 65),
    ("GBR", "CHN", 95),
    ("CHN", "JPN", 280),
    ("CHN", "KOR", 250),
    ("CHN", "AUS", 180),
    ("CHN", "IND", 100),
    ("JPN", "KOR", 70),
    ("JPN", "AUS", 55),
    ("IND", "AUS", 30),
    ("BRA", "DEU", 20),
]

# Force-directed layout computation
node_list = list(nodes.keys())
n = len(node_list)
node_idx = {name: i for i, name in enumerate(node_list)}

# Initialize positions randomly
pos = np.random.rand(n, 2) * 2 - 1

k = 1.5 / np.sqrt(n)  # Optimal distance
t = 0.5  # Temperature (step size)

for _ in range(300):
    disp = np.zeros((n, 2))

    # Repulsive forces between all pairs
    for i in range(n):
        for j in range(i + 1, n):
            delta = pos[i] - pos[j]
            dist = max(np.linalg.norm(delta), 0.01)
            force = k * k / dist * 1.5
            direction = delta / dist
            disp[i] += direction * force
            disp[j] -= direction * force

    # Attractive forces along edges (weighted)
    for src, tgt, weight in edges:
        i, j = node_idx[src], node_idx[tgt]
        delta = pos[i] - pos[j]
        dist = max(np.linalg.norm(delta), 0.01)
        force = dist * dist / k * (0.8 + weight / 400)
        direction = delta / dist
        disp[i] -= direction * force
        disp[j] += direction * force

    # Apply displacement with temperature limiting
    for i in range(n):
        disp_norm = max(np.linalg.norm(disp[i]), 0.01)
        pos[i] += disp[i] / disp_norm * min(disp_norm, t)

    t *= 0.97

# Normalize positions to [2, 10] for pygal
pos_min = pos.min(axis=0)
pos_max = pos.max(axis=0)
pos = (pos - pos_min) / (pos_max - pos_min + 1e-6) * 8 + 2
positions = {name: pos[node_idx[name]] for name in node_list}

# Compute weighted degree for node sizing
weighted_degree = dict.fromkeys(nodes, 0)
for src, tgt, weight in edges:
    weighted_degree[src] += weight
    weighted_degree[tgt] += weight

max_degree = max(weighted_degree.values())
min_degree = min(weighted_degree.values())

# Color mapping by region
group_colors = {
    "Americas": "#306998",  # Python Blue
    "Europe": "#1A1A1A",  # Near black (high contrast)
    "Asia": "#FFD43B",  # Python Yellow
    "Oceania": "#E74C3C",  # Red
}

# Bin edges by weight for visual thickness representation
edge_weights = [w for _, _, w in edges]
min_weight = min(edge_weights)
max_weight = max(edge_weights)
weight_range = max_weight - min_weight

# Create 4 weight bins for edge thickness visualization
edge_bins = {
    "low": [],  # 0-25% percentile: $20-178B
    "medium": [],  # 25-50%: $178-335B
    "high": [],  # 50-75%: $335-493B
    "very_high": [],  # 75-100%: $493-650B
}

for src, tgt, weight in edges:
    norm_weight = (weight - min_weight) / weight_range if weight_range > 0 else 0.5
    if norm_weight < 0.25:
        edge_bins["low"].append((src, tgt, weight))
    elif norm_weight < 0.5:
        edge_bins["medium"].append((src, tgt, weight))
    elif norm_weight < 0.75:
        edge_bins["high"].append((src, tgt, weight))
    else:
        edge_bins["very_high"].append((src, tgt, weight))

# Edge thickness settings (stroke-width in pixels) - dramatically different for visibility
edge_styles = {
    "low": {"stroke": "#CCCCCC", "stroke_width": 3},
    "medium": {"stroke": "#999999", "stroke_width": 10},
    "high": {"stroke": "#666666", "stroke_width": 20},
    "very_high": {"stroke": "#222222", "stroke_width": 32},
}

# Custom style for pygal chart
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=(group_colors["Americas"], group_colors["Europe"], group_colors["Asia"], group_colors["Oceania"]),
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=32,
    stroke_width=3,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create pygal XY chart for nodes (to use pygal's features)
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="network-weighted · pygal · pyplots.ai",
    show_legend=True,
    x_title="",
    y_title="",
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    stroke=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=36,
    range=(0, 12),
    xrange=(0, 12),
    print_labels=True,
    print_values=False,
    margin_bottom=200,
    margin_top=120,
)

# Group nodes by region and add to chart with varying dot sizes based on weighted degree
regions = {"Americas": [], "Europe": [], "Asia": [], "Oceania": []}
for name, data in nodes.items():
    regions[data["group"]].append(name)

for region, region_nodes in regions.items():
    node_points = []
    for name in region_nodes:
        x, y = positions[name]
        # Calculate dot size based on weighted degree (25-65 px)
        degree_norm = (
            (weighted_degree[name] - min_degree) / (max_degree - min_degree) if max_degree > min_degree else 0.5
        )
        dot_size = 25 + degree_norm * 40
        label = name  # Show country code as label
        node_points.append({"value": (x, y), "label": label, "node": {"r": dot_size}})
    chart.add(region, node_points, dots_size=40)

# Render chart to get SVG string
svg_content = chart.render().decode("utf-8")

# Post-process SVG to add edges with varying thickness before nodes
# Find the position to insert edges (after background, before data)

# Find the first <g class="series" position to insert edges before it
series_match = re.search(r'(<g class="series)', svg_content)
if series_match:
    insert_pos = series_match.start()
else:
    # Fallback: insert before </svg>
    insert_pos = svg_content.rfind("</svg>")

# Calculate SVG coordinate transformation (pygal uses viewBox)
# We need to map our data coords to pygal's SVG coords
# Pygal typically maps xrange/range to the plot area
svg_margin = {"top": 120, "right": 100, "bottom": 200, "left": 100}
svg_width = 4800
svg_height = 2700
plot_width = svg_width - svg_margin["left"] - svg_margin["right"]
plot_height = svg_height - svg_margin["top"] - svg_margin["bottom"]

# Build edge SVG elements
edge_svg_parts = ['<g class="edges">']

for weight_cat in ["low", "medium", "high", "very_high"]:
    style = edge_styles[weight_cat]
    for src, tgt, _weight in edge_bins[weight_cat]:
        # Convert data coordinates to SVG coordinates
        x1_data, y1_data = positions[src]
        x2_data, y2_data = positions[tgt]

        x1 = svg_margin["left"] + (x1_data / 12) * plot_width
        y1 = svg_margin["top"] + (1 - y1_data / 12) * plot_height
        x2 = svg_margin["left"] + (x2_data / 12) * plot_width
        y2 = svg_margin["top"] + (1 - y2_data / 12) * plot_height

        edge_svg_parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{style["stroke"]}" stroke-width="{style["stroke_width"]}" '
            f'stroke-linecap="round" opacity="0.7"/>'
        )

edge_svg_parts.append("</g>")
edge_svg = "\n".join(edge_svg_parts)

# Insert edges into SVG
svg_content = svg_content[:insert_pos] + edge_svg + "\n" + svg_content[insert_pos:]

# Add node labels (country codes) on top of nodes with shadow for readability
label_svg_parts = ['<g class="node-labels">']
for name in nodes.keys():
    x_data, y_data = positions[name]
    x = svg_margin["left"] + (x_data / 12) * plot_width
    y = svg_margin["top"] + (1 - y_data / 12) * plot_height
    # Add white background for better visibility over edges
    label_svg_parts.append(
        f'<text x="{x:.1f}" y="{y + 14:.1f}" text-anchor="middle" '
        f'font-family="sans-serif" font-size="46" font-weight="bold" fill="white" '
        f'stroke="white" stroke-width="8">{name}</text>'
    )
    # Main dark text on top
    label_svg_parts.append(
        f'<text x="{x:.1f}" y="{y + 14:.1f}" text-anchor="middle" '
        f'font-family="sans-serif" font-size="46" font-weight="bold" fill="#1A1A1A">{name}</text>'
    )
label_svg_parts.append("</g>")
label_svg = "\n".join(label_svg_parts)

# Insert labels before closing </svg>
svg_content = svg_content.replace("</svg>", label_svg + "\n</svg>")

# Add edge thickness legend with proper spacing to avoid truncation
legend_y = 2700 - 100
legend_x_start = 1800
legend_items = [
    ("$20-178B", edge_styles["low"]),
    ("$178-335B", edge_styles["medium"]),
    ("$335-493B", edge_styles["high"]),
    ("$493-650B", edge_styles["very_high"]),
]

edge_legend_parts = ['<g class="edge-legend">']
edge_legend_parts.append(
    f'<text x="{legend_x_start}" y="{legend_y + 12}" '
    f'font-family="sans-serif" font-size="36" font-weight="bold" fill="#333333">Edge weights:</text>'
)
legend_x = legend_x_start + 280
for label, style in legend_items:
    edge_legend_parts.append(
        f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 60}" y2="{legend_y}" '
        f'stroke="{style["stroke"]}" stroke-width="{style["stroke_width"]}" stroke-linecap="round"/>'
    )
    edge_legend_parts.append(
        f'<text x="{legend_x + 80}" y="{legend_y + 12}" '
        f'font-family="sans-serif" font-size="32" fill="#333333">{label}</text>'
    )
    legend_x += 360
edge_legend_parts.append("</g>")
edge_legend_svg = "\n".join(edge_legend_parts)

# Insert edge legend before closing </svg>
svg_content = svg_content.replace("</svg>", edge_legend_svg + "\n</svg>")

# Convert modified SVG to PNG using cairosvg
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to="plot.png")
