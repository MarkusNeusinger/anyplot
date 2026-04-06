""" pyplots.ai
chord-basic: Basic Chord Diagram
Library: pygal 3.1.0 | Python 3.14
Quality: 70/100 | Updated: 2026-04-06
"""

import math

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data: Migration flows between 6 continents (thousands of people)
continents = ["Africa", "Asia", "Europe", "N. America", "S. America", "Oceania"]
n_entities = len(continents)

# Bidirectional migration flows (source_idx, target_idx, value)
flows = [
    (0, 1, 8),
    (0, 2, 25),
    (0, 3, 12),
    (0, 4, 5),
    (0, 5, 3),
    (1, 0, 6),
    (1, 2, 20),
    (1, 3, 35),
    (1, 4, 8),
    (1, 5, 18),
    (2, 0, 4),
    (2, 1, 12),
    (2, 3, 22),
    (2, 4, 15),
    (2, 5, 10),
    (3, 0, 2),
    (3, 1, 10),
    (3, 2, 18),
    (3, 4, 14),
    (3, 5, 6),
    (4, 0, 3),
    (4, 1, 7),
    (4, 2, 28),
    (4, 3, 20),
    (4, 5, 4),
    (5, 0, 2),
    (5, 1, 15),
    (5, 2, 12),
    (5, 3, 8),
    (5, 4, 3),
]

# Colorblind-safe palette per continent
entity_colors = [
    "#306998",  # Africa - Python Blue
    "#FFD43B",  # Asia - Gold
    "#4CAF50",  # Europe - Green
    "#FF7043",  # N. America - Orange
    "#9C27B0",  # S. America - Purple
    "#00BCD4",  # Oceania - Cyan
]

# Circle geometry - use more of the canvas
center = 5.0
chord_radius = 3.2
node_radius = 3.55
label_radius = 4.15

angles = [2 * math.pi * i / n_entities - math.pi / 2 for i in range(n_entities)]

# Build color sequence: one per chord (source color), then one per continent for legend
chord_colors = [entity_colors[src] for src, _, _ in flows]
all_colors = tuple(chord_colors + entity_colors)

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#999999",
    colors=all_colors,
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
    opacity=0.45,
    opacity_hover=0.95,
)

# XY chart as canvas (square for circular diagram)
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="chord-basic \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=True,
    x_title="",
    y_title="",
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    stroke=True,
    dots_size=0,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
    legend_box_size=24,
    range=(0, 10),
    xrange=(0, 10),
    truncate_legend=-1,
)

# Flow stats for stroke scaling
max_flow = max(v for _, _, v in flows)
min_flow = min(v for _, _, v in flows)

# Draw chords as quadratic Bezier curves
for src, tgt, val in flows:
    sa, ta = angles[src], angles[tgt]
    sx = center + chord_radius * math.cos(sa)
    sy = center + chord_radius * math.sin(sa)
    tx = center + chord_radius * math.cos(ta)
    ty = center + chord_radius * math.sin(ta)

    # Control point pulled toward center for pronounced curvature
    mid_x, mid_y = (sx + tx) / 2, (sy + ty) / 2
    pull = 0.08
    ctrl_x = center + pull * (mid_x - center)
    ctrl_y = center + pull * (mid_y - center)

    curve = []
    for t in np.linspace(0, 1, 60):
        bx = (1 - t) ** 2 * sx + 2 * (1 - t) * t * ctrl_x + t**2 * tx
        by = (1 - t) ** 2 * sy + 2 * (1 - t) * t * ctrl_y + t**2 * ty
        curve.append((bx, by))

    # Stroke width 4-22 proportional to flow value
    normalized = (val - min_flow) / (max_flow - min_flow) if max_flow > min_flow else 0.5
    stroke_w = 4 + normalized * 18

    chart.add(
        None, curve, stroke=True, show_dots=False, fill=False, stroke_style={"width": stroke_w, "linecap": "round"}
    )

# Draw prominent node arcs on the perimeter (also serve as legend entries)
for i, continent in enumerate(continents):
    arc_span = 0.32
    node_points = []
    for t in np.linspace(-arc_span, arc_span, 25):
        nx = center + node_radius * math.cos(angles[i] + t)
        ny = center + node_radius * math.sin(angles[i] + t)
        node_points.append((nx, ny))

    chart.add(
        continent, node_points, stroke=True, show_dots=False, fill=False, stroke_style={"width": 26, "linecap": "round"}
    )

# Render base SVG
chart.render_to_file("plot.svg")

# Inject colored text labels near each node
with open("plot.svg") as f:
    svg_content = f.read()

label_svg = ""
padding = 550
plot_size = 2500
for i, continent in enumerate(continents):
    lx = center + label_radius * math.cos(angles[i])
    ly = center + label_radius * math.sin(angles[i])
    svg_x = padding + (lx / 10) * plot_size
    svg_y = padding + ((10 - ly) / 10) * plot_size

    angle_deg = math.degrees(angles[i])
    if -60 <= angle_deg <= 60:
        anchor, svg_x = "start", svg_x + 45
    elif angle_deg > 120 or angle_deg < -120:
        anchor, svg_x = "end", svg_x - 45
    else:
        anchor = "middle"

    if -30 <= angle_deg <= 30 or angle_deg > 150 or angle_deg < -150:
        svg_y += 18

    label_svg += (
        f'  <text x="{svg_x:.0f}" y="{svg_y:.0f}" fill="{entity_colors[i]}"'
        f' font-size="56" font-weight="bold" text-anchor="{anchor}"'
        f' font-family="DejaVu Sans, sans-serif">{continent}</text>\n'
    )

svg_with_labels = svg_content.replace("</svg>", f"{label_svg}</svg>")

with open("plot.svg", "w") as f:
    f.write(svg_with_labels)

# Render PNG from final SVG
cairosvg.svg2png(bytestring=svg_with_labels.encode("utf-8"), write_to="plot.png")

# Interactive HTML version
with open("plot.html", "w") as f:
    f.write(
        "<!DOCTYPE html>\n<html>\n<head>\n"
        "    <title>chord-basic \u00b7 pygal \u00b7 pyplots.ai</title>\n"
        "    <style>\n"
        "        body { margin: 0; padding: 20px; background: #f5f5f5; }\n"
        "        .container { max-width: 100%; margin: 0 auto; }\n"
        "        object { width: 100%; height: auto; }\n"
        "    </style>\n</head>\n<body>\n"
        '    <div class="container">\n'
        '        <object type="image/svg+xml" data="plot.svg">'
        "Chord diagram not supported</object>\n"
        "    </div>\n</body>\n</html>"
    )
