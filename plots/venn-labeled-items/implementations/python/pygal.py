""" anyplot.ai
venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
Library: pygal 3.1.0 | Python 3.14.4
Quality: 86/100 | Created: 2026-04-25
"""

import importlib
import math
import os
import re
import sys
from collections import defaultdict


# Drop the script directory from sys.path so the `pygal` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style
cairosvg = importlib.import_module("cairosvg")


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito categorical palette: brand green, vermillion, blue
COLOR_A = "#009E73"
COLOR_B = "#D55E00"
COLOR_C = "#0072B2"

# Symmetric three-circle Venn: equilateral triangle of centers (apex up)
RADIUS = 1.0
OFFSET = RADIUS / math.sqrt(3)
ax, ay = -OFFSET * math.sin(math.radians(60)), -OFFSET * math.cos(math.radians(60))
bx, by = OFFSET * math.sin(math.radians(60)), -OFFSET * math.cos(math.radians(60))
cx, cy = 0.0, OFFSET

circles = [
    {"name": "OVERHYPED", "color": COLOR_A, "center": (ax, ay), "label_xy": (ax - 0.95, ay - 1.10), "anchor": "start"},
    {
        "name": "ACTUALLY USEFUL",
        "color": COLOR_B,
        "center": (bx, by),
        "label_xy": (bx + 0.95, by - 1.10),
        "anchor": "end",
    },
    {"name": "SECRETLY LOVED", "color": COLOR_C, "center": (cx, cy), "label_xy": (cx, cy + 1.18), "anchor": "middle"},
]

# Items distributed across the seven interior zones
items_raw = [
    ("NFTs", "A"),
    ("Metaverse", "A"),
    ("Web3", "A"),
    ("Google Maps", "B"),
    ("Sticky Notes", "B"),
    ("USB Hubs", "B"),
    ("Karaoke", "C"),
    ("Postcards", "C"),
    ("Smartphones", "AB"),
    ("Email", "AB"),
    ("Crocs", "AC"),
    ("Pumpkin Spice", "AC"),
    ("Spotify", "BC"),
    ("Dolly Parton", "BC"),
    ("Sourdough", "ABC"),
    ("TikTok", "ABC"),
]

# Centroids of each Venn region in chart-data units
zone_centers = {
    "A": (ax - 0.55, ay + 0.05),
    "B": (bx + 0.55, by + 0.05),
    "C": (cx, cy + 0.50),
    "AB": (0.0, by - 0.32),
    "AC": (-0.45, 0.20),
    "BC": (0.45, 0.20),
    "ABC": (0.0, -0.05),
}

LINE_HEIGHT = 0.13
zone_to_items = defaultdict(list)
for label, zone in items_raw:
    zone_to_items[zone].append(label)

item_points = []
for zone, labels in zone_to_items.items():
    zx, zy = zone_centers[zone]
    n = len(labels)
    start_y = zy + (n - 1) * LINE_HEIGHT / 2
    for i, label in enumerate(labels):
        item_points.append({"value": (zx, start_y - i * LINE_HEIGHT), "label": label})


# Parametric points for a circle outline (closed polyline)
def circle_outline(center, r, n=120):
    cx0, cy0 = center
    return [(cx0 + r * math.cos(2 * math.pi * i / n), cy0 + r * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]


# Style — derived from theme tokens
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(COLOR_A, COLOR_B, COLOR_C, INK, INK, INK, INK),
    opacity="1",
    opacity_hover="1",
    stroke_width=6,
    stroke_opacity=".90",
    stroke_opacity_hover=".90",
    title_font_size=72,
    label_font_size=22,
    major_label_font_size=22,
    legend_font_size=22,
    value_font_size=42,
    value_label_font_size=42,
    title_font_family="serif",
    label_font_family="serif",
    major_label_font_family="serif",
    legend_font_family="serif",
    value_font_family="serif",
    value_label_font_family="serif",
    transition="0",
)

# Plot — square 3600×3600 canvas suits the radial Venn layout
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="Pop Culture Vibes 2026 · venn-labeled-items · pygal · anyplot.ai",
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    show_minor_x_labels=False,
    show_minor_y_labels=False,
    xrange=(-2.30, 2.30),
    range=(-2.30, 2.30),
    margin=20,
    spacing=0,
    show_dots=True,
    dots_size=0,
    print_labels=True,
    print_values=False,
    pretty_print=True,
)

# Three circle outlines (one series per circle) — fills are added via post-processing
for c in circles:
    chart.add("", circle_outline(c["center"], RADIUS), stroke=True, fill=False, show_dots=False)

# Item names — text-only placement at zone centroids
chart.add("Items", item_points, stroke=False, show_dots=True)

# Category names — same labeling mechanism, restyled by post-processor below
for c in circles:
    chart.add("", [{"value": c["label_xy"], "label": c["name"]}], stroke=False, show_dots=True)

svg = chart.render().decode("utf-8")


# Post-process — pygal cannot natively (a) fill a closed polyline or (b) per-label
# typography. Both are added directly to the SVG output.
def fill_circle_path(svg_text, serie_idx, color, opacity):
    pattern = re.compile(
        r'(<g class="series serie-' + str(serie_idx) + r' color-\d+">\s*<path[^>]*?)class="line reactive nofill"'
    )
    return pattern.sub(
        r'\1class="line reactive" style="fill:' + color + ";fill-opacity:" + str(opacity) + r';stroke-width:7"',
        svg_text,
        count=1,
    )


for idx, c in enumerate(circles):
    svg = fill_circle_path(svg, idx, c["color"], 0.18)


# Restyle category labels by matching their text content
def restyle_label(svg_text, label_text, color, anchor, font_size):
    pattern = re.compile(r'<text(\s+x="[^"]*"\s+y="[^"]*")\s+class="label">' + re.escape(label_text) + r"</text>")
    return pattern.sub(
        r'<text\1 class="label" style="font-size:'
        + str(font_size)
        + ";font-style:italic;font-weight:bold;text-anchor:"
        + anchor
        + ";fill:"
        + color
        + r'">'
        + label_text
        + "</text>",
        svg_text,
        count=1,
    )


for c in circles:
    svg = restyle_label(svg, c["name"], c["color"], c["anchor"], 64)

# Pygal auto-picks white text whenever a series color is dark — that turns
# the item labels invisible on our cream/charcoal background. Rewrite those
# rules in place so labels inherit the theme INK instead.
svg = re.sub(r"(\.text-overlay \.color-\d+ text \{\s*fill:\s*)[^;}\s]+", r"\1" + INK, svg)
# Bump the rendered label size to the 42px set in Style above; pygal's
# CSS hard-codes 36px ignoring `value_label_font_size` for XY plots.
svg = re.sub(r"(\.text-overlay text\.label \{[^}]*font-size:\s*)\d+px", r"\g<1>42px", svg)

# Editorial subtitle injected at a fixed canvas position, theme-aware
subtitle = (
    '<g class="anyplot-subtitle"><text x="1800" y="3540" '
    'style="font-family:serif;font-style:italic;font-size:42px;fill:' + INK_SOFT + ';text-anchor:middle">'
    "A field guide to sixteen things, three feelings, and seven overlapping truths"
    "</text></g>"
)
svg = svg.replace("</svg>", subtitle + "</svg>")


# Save — interactive SVG embedded in HTML, plus rasterized PNG via cairosvg
with open(f"plot-{THEME}.svg", "w") as f:
    f.write(svg)

with open(f"plot-{THEME}.html", "w") as f:
    f.write("<!doctype html><html><body style='margin:0;background:" + PAGE_BG + "'>" + svg + "</body></html>")

cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=3600, output_height=3600)
