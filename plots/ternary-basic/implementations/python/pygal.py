""" pyplots.ai
ternary-basic: Basic Ternary Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 78/100 | Created: 2025-12-24
"""

import math

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


np.random.seed(42)

# Triangle height for equilateral triangle with base = 1
H = math.sqrt(3) / 2

# Sample soil composition data (Sand%, Silt%, Clay%) - all sum to 100
# Ternary coordinates: Top=Sand, Bottom-right=Silt, Bottom-left=Clay
compositions = [
    (65, 25, 10),  # Sandy Loam
    (10, 45, 45),  # Silty Clay
    (30, 35, 35),  # Clay Loam
    (40, 40, 20),  # Loam
    (50, 10, 40),  # Sandy Clay
    (20, 65, 15),  # Silt Loam
    (90, 5, 5),  # Pure Sand
    (5, 90, 5),  # Pure Silt
    (5, 5, 90),  # Pure Clay
    (33, 34, 33),  # Balanced
    (45, 45, 10),  # Sandy Silt
    (55, 35, 10),  # Silty Sand
    (15, 20, 65),  # Clay
    (10, 15, 75),  # Heavy Clay
    (50, 30, 20),  # Light Loam
]

# Convert ternary (sand, silt, clay) to cartesian (x, y)
# Formula: x = 0.5 * (2 * silt/100 + sand/100), y = H * sand/100
data_points = [(0.5 * (2 * s[1] + s[0]) / 100, H * s[0] / 100) for s in compositions]

# Triangle vertices
vertex_sand = (0.5, H)  # Top - 100% Sand
vertex_silt = (1.0, 0.0)  # Bottom-right - 100% Silt
vertex_clay = (0.0, 0.0)  # Bottom-left - 100% Clay

# Grid lines at 20%, 40%, 60%, 80% intervals
# Each line connects two edges of the triangle
grid_lines = []
for pct in [0.2, 0.4, 0.6, 0.8]:
    # Parallel to base (constant Sand %) - from left edge to right edge
    p1 = (0.5 * (2 * (1 - pct) + pct), H * pct)
    p2 = (0.5 * pct, H * pct)
    grid_lines.extend([p1, p2, (None, None)])

    # Parallel to left side (constant Silt %) - from base to right edge
    p1 = (0.5 * (2 * pct + (1 - pct)), H * (1 - pct))
    p2 = (pct, 0.0)
    grid_lines.extend([p1, p2, (None, None)])

    # Parallel to right side (constant Clay %) - from base to left edge
    p1 = (0.5 * (1 - pct), H * (1 - pct))
    p2 = (0.5 * (2 * (1 - pct)), 0.0)
    grid_lines.extend([p1, p2, (None, None)])

# Tick marks along each edge at 20% intervals
tick_marks = []
tick_len = 0.03  # Length of tick marks

for pct in [0.2, 0.4, 0.6, 0.8]:
    # Ticks on left edge (Clay-Sand): perpendicular outward
    x_left = 0.5 * pct
    y_left = H * pct
    tick_marks.extend([(x_left, y_left), (x_left - tick_len, y_left), (None, None)])

    # Ticks on right edge (Sand-Silt): perpendicular outward
    x_right = 0.5 * (2 - pct)
    y_right = H * pct
    tick_marks.extend([(x_right, y_right), (x_right + tick_len, y_right), (None, None)])

    # Ticks on base (Clay-Silt): perpendicular downward
    x_base = pct
    y_base = 0.0
    tick_marks.extend([(x_base, y_base), (x_base, y_base - tick_len), (None, None)])

# Custom style for 3600x3600 px canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#333333", "#AAAAAA", "#306998", "#333333"),  # Boundary, Grid, Data, Ticks
    title_font_size=80,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=40,
    opacity=0.85,
)

# Create XY chart (square format for ternary plot)
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    x_title="",
    y_title="",
    title="Soil Composition · ternary-basic · pygal · pyplots.ai",
    dots_size=20,
    stroke=False,
    include_x_axis=False,
    xrange=(-0.15, 1.15),
    yrange=(-0.20, 1.05),
    explicit_size=True,
    margin=50,
    margin_bottom=120,
)

# Triangle outline (no legend entry - structural element)
chart.add(
    None, [vertex_clay, vertex_silt, vertex_sand, vertex_clay], stroke=True, show_dots=False, stroke_style={"width": 5}
)

# Grid lines at 20% intervals (no legend entry - structural element)
chart.add(None, grid_lines, stroke=True, show_dots=False, stroke_style={"width": 2, "dasharray": "8,5"})

# Data points (soil samples) - the only legend-worthy series
chart.add("Soil Samples", data_points, stroke=False, dots_size=22)

# Tick marks along edges (no legend entry - structural element)
chart.add(None, tick_marks, stroke=True, show_dots=False, stroke_style={"width": 3})

# Render to SVG string first
svg_content = chart.render().decode("utf-8")

# Calculate pixel positions for labels (inline conversion - KISS principle)
# The chart has xrange=(-0.15, 1.15) = 1.30 range and yrange=(-0.20, 1.05) = 1.25 range
# Approximate: plot area starts after margin and title
plot_x_start = 150
plot_x_end = 3450
plot_y_start = 250
plot_y_end = 3350
x_range = 1.30
y_range = 1.25

# Vertex label positions (offset from triangle vertices)
sand_px = plot_x_start + (0.5 + 0.15) / x_range * (plot_x_end - plot_x_start)
sand_py = plot_y_start + (1.05 - (H + 0.06)) / y_range * (plot_y_end - plot_y_start)
silt_px = plot_x_start + (1.07 + 0.15) / x_range * (plot_x_end - plot_x_start)
silt_py = plot_y_start + (1.05 - (-0.03)) / y_range * (plot_y_end - plot_y_start)
clay_px = plot_x_start + (-0.07 + 0.15) / x_range * (plot_x_end - plot_x_start)
clay_py = plot_y_start + (1.05 - (-0.03)) / y_range * (plot_y_end - plot_y_start)

# Build SVG text elements for vertex labels
vertex_labels_svg = f"""
  <text x="{sand_px}" y="{sand_py}" text-anchor="middle" font-size="60" font-weight="bold" fill="#333333" font-family="sans-serif">SAND</text>
  <text x="{silt_px}" y="{silt_py}" text-anchor="start" font-size="60" font-weight="bold" fill="#333333" font-family="sans-serif">SILT</text>
  <text x="{clay_px}" y="{clay_py}" text-anchor="end" font-size="60" font-weight="bold" fill="#333333" font-family="sans-serif">CLAY</text>
"""

# Percentage labels along each edge at 20%, 40%, 60%, 80%
pct_labels_svg = ""
pct_font_size = 36

for pct in [20, 40, 60, 80]:
    frac = pct / 100.0

    # Left edge (Clay-Sand): Sand % increases going up, Clay % decreases
    left_x = 0.5 * frac
    left_y = H * frac
    left_px = plot_x_start + (left_x - 0.06 + 0.15) / x_range * (plot_x_end - plot_x_start)
    left_py = plot_y_start + (1.05 - left_y) / y_range * (plot_y_end - plot_y_start)
    pct_labels_svg += f'  <text x="{left_px}" y="{left_py}" text-anchor="end" font-size="{pct_font_size}" fill="#666666" font-family="sans-serif">{pct}</text>\n'

    # Right edge (Sand-Silt): Sand % increases going up, Silt % increases going down-right
    right_x = 0.5 * (2 - frac)
    right_y = H * frac
    right_px = plot_x_start + (right_x + 0.04 + 0.15) / x_range * (plot_x_end - plot_x_start)
    right_py = plot_y_start + (1.05 - right_y) / y_range * (plot_y_end - plot_y_start)
    pct_labels_svg += f'  <text x="{right_px}" y="{right_py}" text-anchor="start" font-size="{pct_font_size}" fill="#666666" font-family="sans-serif">{pct}</text>\n'

    # Bottom edge (Clay-Silt): Clay % decreases left-to-right, Silt % increases
    base_x = frac
    base_y = -0.05
    base_px = plot_x_start + (base_x + 0.15) / x_range * (plot_x_end - plot_x_start)
    base_py = plot_y_start + (1.05 - base_y) / y_range * (plot_y_end - plot_y_start)
    pct_labels_svg += f'  <text x="{base_px}" y="{base_py}" text-anchor="middle" font-size="{pct_font_size}" fill="#666666" font-family="sans-serif">{pct}</text>\n'

# Insert all labels before the closing </svg> tag
all_labels_svg = vertex_labels_svg + pct_labels_svg
svg_content = svg_content.replace("</svg>", all_labels_svg + "</svg>")

# Save as SVG for HTML output
with open("plot.html", "w") as f:
    f.write(svg_content)

# Convert to PNG
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to="plot.png")
