""" pyplots.ai
icicle-basic: Basic Icicle Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import xml.etree.ElementTree as ET

import cairosvg
import pygal
from pygal.style import Style


# Data: File system structure with folders and files
# Format: (name, parent, value) - leaf nodes have values, internal nodes computed
hierarchy_data = [
    ("Root", None, 0),
    ("Documents", "Root", 0),
    ("Pictures", "Root", 0),
    ("Music", "Root", 0),
    ("Reports", "Documents", 0),
    ("Letters", "Documents", 0),
    ("Spreadsheets", "Documents", 0),
    ("Photos", "Pictures", 0),
    ("Screenshots", "Pictures", 0),
    ("Icons", "Pictures", 0),
    ("Albums", "Music", 0),
    ("Playlists", "Music", 0),
    ("Podcasts", "Music", 0),
    ("Q1_Report", "Reports", 45),
    ("Q2_Report", "Reports", 55),
    ("Q3_Report", "Reports", 50),
    ("Cover_Letter", "Letters", 25),
    ("Resume", "Letters", 35),
    ("Thank_You", "Letters", 20),
    ("Budget", "Spreadsheets", 60),
    ("Forecast", "Spreadsheets", 40),
    ("Analysis", "Spreadsheets", 20),
    ("Photo_1", "Photos", 65),
    ("Photo_2", "Photos", 75),
    ("Photo_3", "Photos", 60),
    ("Screen_1", "Screenshots", 25),
    ("Screen_2", "Screenshots", 25),
    ("Icon_1", "Icons", 35),
    ("Icon_2", "Icons", 35),
    ("Rock", "Albums", 60),
    ("Jazz", "Albums", 55),
    ("Pop", "Albums", 65),
    ("Favorites", "Playlists", 40),
    ("Podcast_1", "Podcasts", 45),
    ("Podcast_2", "Podcasts", 45),
]

# Build tree structure
nodes = {}
children = {}

for name, parent, value in hierarchy_data:
    nodes[name] = {"name": name, "parent": parent, "value": value}
    if parent is not None:
        if parent not in children:
            children[parent] = []
        children[parent].append(name)

# Calculate total values for all nodes (bottom-up traversal)
# Get nodes in depth order using BFS
node_depths = {"Root": 0}
queue = ["Root"]
depth_order = []
while queue:
    current = queue.pop(0)
    depth_order.append(current)
    if current in children:
        for child in children[current]:
            node_depths[child] = node_depths[current] + 1
            queue.append(child)

# Calculate values bottom-up
node_values = {}
for node_name in reversed(depth_order):
    if node_name not in children:
        node_values[node_name] = nodes[node_name]["value"]
    else:
        node_values[node_name] = sum(node_values[child] for child in children[node_name])

# Calculate positions for icicle chart (top-to-bottom layout)
positions = {}
positions["Root"] = {"x_start": 0, "x_end": 1, "depth": 0, "value": node_values["Root"]}

# Process nodes level by level
for node_name in depth_order:
    if node_name in children:
        pos = positions[node_name]
        current_x = pos["x_start"]
        total_value = node_values[node_name]
        for child in children[node_name]:
            child_value = node_values[child]
            child_width = (child_value / total_value) * (pos["x_end"] - pos["x_start"])
            positions[child] = {
                "x_start": current_x,
                "x_end": current_x + child_width,
                "depth": pos["depth"] + 1,
                "value": child_value,
            }
            current_x += child_width

# Find max depth
max_depth = max(pos["depth"] for pos in positions.values())

# Chart dimensions (landscape format for icicle chart)
WIDTH = 4800
HEIGHT = 2700
MARGIN_TOP = 120
MARGIN_BOTTOM = 100
MARGIN_LEFT = 50
MARGIN_RIGHT = 200  # Space for level labels
PLOT_WIDTH = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
PLOT_HEIGHT = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

# Color palette by depth level (colorblind-safe)
DEPTH_COLORS = [
    "#306998",  # Python Blue - Level 0
    "#FFD43B",  # Python Yellow - Level 1
    "#4ECDC4",  # Teal - Level 2
    "#FF6B6B",  # Coral - Level 3
    "#95E1D3",  # Light teal - Level 4
]

# Text colors for each depth (white on dark, black on light)
TEXT_COLORS = ["white", "#333333", "#333333", "white", "#333333"]

# Use pygal Style for consistent theming
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=DEPTH_COLORS,
    title_font_size=72,
    label_font_size=42,
    major_label_font_size=36,
    legend_font_size=36,
    font_family="sans-serif",
)

# Create base pygal config (used for style extraction)
config = pygal.Config()
config.width = WIDTH
config.height = HEIGHT
config.style = custom_style

# Build SVG using standard library
svg_ns = "http://www.w3.org/2000/svg"
ET.register_namespace("", svg_ns)

svg_root = ET.Element("svg", xmlns=svg_ns, width=str(WIDTH), height=str(HEIGHT), viewBox=f"0 0 {WIDTH} {HEIGHT}")
svg_root.set("style", f"background-color: {custom_style.background};")

# Add title
title_elem = ET.SubElement(svg_root, "text")
title_elem.set("x", str(WIDTH / 2))
title_elem.set("y", "70")
title_elem.set("text-anchor", "middle")
title_elem.set("fill", custom_style.foreground_strong)
title_elem.set("font-size", str(custom_style.title_font_size))
title_elem.set("font-family", custom_style.font_family)
title_elem.set("font-weight", "bold")
title_elem.text = "icicle-basic · pygal · pyplots.ai"

# Create main group for rectangles
g = ET.SubElement(svg_root, "g")
g.set("class", "icicle-chart")

# Draw rectangles
row_height = PLOT_HEIGHT / (max_depth + 1)
gap = 3  # Small gap between rectangles

for node_name, pos in positions.items():
    depth = pos["depth"]
    x_start = pos["x_start"]
    x_end = pos["x_end"]
    width = x_end - x_start

    # Calculate pixel positions
    px_x = MARGIN_LEFT + x_start * PLOT_WIDTH
    px_width = width * PLOT_WIDTH - gap
    px_y = MARGIN_TOP + depth * row_height
    px_height = row_height - gap

    # Get color based on depth
    color = DEPTH_COLORS[depth % len(DEPTH_COLORS)]

    # Create rectangle element
    rect = ET.SubElement(g, "rect")
    rect.set("x", f"{px_x:.1f}")
    rect.set("y", f"{px_y:.1f}")
    rect.set("width", f"{max(0, px_width):.1f}")
    rect.set("height", f"{px_height:.1f}")
    rect.set("fill", color)
    rect.set("fill-opacity", "0.85")
    rect.set("stroke", "white")
    rect.set("stroke-width", "2")

    # Add tooltip
    title = ET.SubElement(rect, "title")
    title.text = f"{node_name.replace('_', ' ')}: {pos['value']}"

    # Add label if rectangle is wide enough
    if px_width > 60:
        label = node_name.replace("_", " ")
        # Calculate max characters based on width
        max_chars = max(3, int(px_width / 22))
        if len(label) > max_chars:
            label = label[: max_chars - 2] + ".."

        # Calculate font size based on width
        fontsize = min(36, max(18, int(px_width / 6)))

        text = ET.SubElement(g, "text")
        text.set("x", f"{px_x + px_width / 2:.1f}")
        text.set("y", f"{px_y + px_height / 2 + fontsize / 3:.1f}")
        text.set("text-anchor", "middle")
        text.set("fill", TEXT_COLORS[depth % len(TEXT_COLORS)])
        text.set("font-size", str(fontsize))
        text.set("font-family", custom_style.font_family)
        text.set("font-weight", "bold")
        text.text = label

# Add depth level labels on the right
level_labels = ["Root", "Category", "Subcategory", "Item", "Detail"]
labels_g = ET.SubElement(svg_root, "g")
labels_g.set("class", "level-labels")

for depth in range(max_depth + 1):
    y_pos = MARGIN_TOP + depth * row_height + row_height / 2
    level_label = level_labels[depth] if depth < len(level_labels) else f"Level {depth}"

    text = ET.SubElement(labels_g, "text")
    text.set("x", str(MARGIN_LEFT + PLOT_WIDTH + 25))
    text.set("y", f"{y_pos + 10:.1f}")
    text.set("fill", custom_style.foreground_strong)
    text.set("font-size", str(custom_style.major_label_font_size))
    text.set("font-family", custom_style.font_family)
    text.text = level_label

# Add legend at bottom
legend_y = HEIGHT - 50
legend_items = [
    ("Root", DEPTH_COLORS[0]),
    ("Category", DEPTH_COLORS[1]),
    ("Subcategory", DEPTH_COLORS[2]),
    ("Item", DEPTH_COLORS[3]),
]
legend_x_start = WIDTH / 2 - 550

legend_g = ET.SubElement(svg_root, "g")
legend_g.set("class", "legend")

for i, (label, color) in enumerate(legend_items):
    x = legend_x_start + i * 300
    # Rectangle marker
    marker = ET.SubElement(legend_g, "rect")
    marker.set("x", str(x))
    marker.set("y", str(legend_y - 15))
    marker.set("width", "30")
    marker.set("height", "30")
    marker.set("fill", color)
    marker.set("stroke", "#444")
    marker.set("stroke-width", "1")
    # Label
    lbl = ET.SubElement(legend_g, "text")
    lbl.set("x", str(x + 40))
    lbl.set("y", str(legend_y + 6))
    lbl.set("fill", custom_style.foreground_strong)
    lbl.set("font-size", str(custom_style.legend_font_size))
    lbl.set("font-family", custom_style.font_family)
    lbl.text = label

# Write SVG to file (pygal convention for interactive output)
svg_output = ET.tostring(svg_root, encoding="unicode")
with open("plot.html", "w") as f:
    f.write(svg_output)

# Render to PNG via cairosvg
cairosvg.svg2png(bytestring=svg_output.encode("utf-8"), write_to="plot.png")
