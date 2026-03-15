""" pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: pygal 3.1.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-15
"""

import re
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data - Alpine hiking trail elevation profile (120 km transect, sampled every ~1 km)
np.random.seed(42)

distances_km = np.linspace(0, 120, 200)

# Build realistic terrain with multiple peaks and valleys
base_terrain = (
    800
    + 600 * np.sin(distances_km * np.pi / 40) ** 2
    + 400 * np.sin(distances_km * np.pi / 25 + 1.2) ** 2
    + 300 * np.exp(-((distances_km - 55) ** 2) / 80)
    + 500 * np.exp(-((distances_km - 85) ** 2) / 120)
    - 200 * np.exp(-((distances_km - 30) ** 2) / 50)
)
noise = np.random.normal(0, 25, len(distances_km))
elevation_m = base_terrain + noise
elevation_m = np.maximum(elevation_m, 650)

# Landmarks along the trail with types for visual differentiation
landmarks = [
    {"name": "Grindelwald", "km": 0, "type": "town"},
    {"name": "Kleine Scheidegg", "km": 22, "type": "pass"},
    {"name": "Lauterbrunnen", "km": 38, "type": "valley"},
    {"name": "Mürren", "km": 55, "type": "summit"},
    {"name": "Blüemlisalp Hut", "km": 72, "type": "hut"},
    {"name": "Hohtürli Pass", "km": 85, "type": "pass"},
    {"name": "Kandersteg", "km": 120, "type": "town"},
]

# Get elevation at landmark positions
for lm in landmarks:
    idx = np.argmin(np.abs(distances_km - lm["km"]))
    lm["elev"] = float(elevation_m[idx])

# Visual styling per landmark type
TYPE_COLORS = {
    "summit": "#b5342b",  # deep red for highest point
    "pass": "#c45a00",  # orange for mountain passes
    "hut": "#7b4ea0",  # purple for alpine huts (distinct from orange)
    "valley": "#2a7f3f",  # green for valley floors
    "town": "#306998",  # blue for towns/settlements
}

# Custom style with refined palette
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2d2d2d",
    foreground_strong="#2d2d2d",
    foreground_subtle="#e8e8e8",
    colors=("#4a7fb5", "#d4690e"),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=48,
    label_font_size=36,
    major_label_font_size=34,
    value_font_size=28,
    legend_font_size=30,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    major_label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    opacity=0.65,
    opacity_hover=0.75,
    guide_stroke_color="#e8e8e8",
    guide_stroke_dasharray="4,4",
    major_guide_stroke_color="#d0d0d0",
    major_guide_stroke_dasharray="6,4",
    stroke_opacity=1.0,
    stroke_opacity_hover=1.0,
    tooltip_font_size=26,
    tooltip_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    tooltip_border_radius=8,
)

# Chart - tightened y-range to frame data better (peak ~2009m)
chart = pygal.XY(
    width=4800,
    height=2700,
    title="Bernese Oberland Traverse · area-elevation-profile · pygal · pyplots.ai",
    x_title="Distance (km)",
    y_title="Elevation (m)",
    style=custom_style,
    fill=True,
    show_dots=False,
    stroke_style={"width": 4},
    show_y_guides=True,
    show_x_guides=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    value_formatter=lambda x: f"{x:,.0f} m",
    x_value_formatter=lambda x: f"{x:.0f} km",
    interpolate="cubic",
    interpolation_precision=300,
    min_scale=5,
    max_scale=10,
    margin_bottom=80,
    margin_left=100,
    margin_right=140,
    margin_top=60,
    spacing=12,
    tooltip_fancy_mode=True,
    range=(500, 2200),
    xrange=(0, 128),
    show_minor_x_labels=False,
    show_minor_y_labels=False,
    truncate_legend=-1,
    dynamic_print_values=True,
    print_values=False,
    show_x_labels=True,
    show_y_labels=True,
    x_labels_major_count=7,
    y_labels_major_count=6,
)

# Elevation profile as filled XY series
profile_data = [
    {"value": (float(d), float(e)), "label": f"{d:.1f} km — {e:.0f} m"}
    for d, e in zip(distances_km, elevation_m, strict=True)
]
chart.add("Elevation Profile", profile_data)

# Landmark markers as separate series with visible dots
landmark_data = [
    {"value": (float(lm["km"]), lm["elev"]), "label": f"{lm['name']} — {lm['elev']:.0f} m"} for lm in landmarks
]
chart.add("Landmarks", landmark_data, fill=False, show_dots=True, dots_size=16, stroke=False)

# Save interactive HTML version with pygal's native tooltip support
chart.render_to_file("plot.html")

# Render SVG for annotation post-processing
svg_bytes = chart.render()
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
root = ET.fromstring(svg_bytes)

# Build parent map and find landmark circles (only dots from the Landmarks series)
parent_map = {child: parent for parent in root.iter() for child in parent}
circles = sorted(
    [c for c in root.iter(f"{{{SVG_NS}}}circle") if float(c.get("r", "0")) > 3], key=lambda c: float(c.get("cx", "0"))
)

# Find plot bottom from horizontal guide paths (format: "M0.0 Y h...")

plot_bottom_y = 0
for path in root.iter(f"{{{SVG_NS}}}path"):
    cls = path.get("class", "")
    d = path.get("d", "")
    if "guide" in cls and " h" in d:
        m = re.match(r"M[\d.]+ ([\d.]+) h", d)
        if m:
            plot_bottom_y = max(plot_bottom_y, float(m.group(1)))

# Label positioning: stagger closely-spaced labels to avoid overlap
label_offsets = {
    "Grindelwald": -42,
    "Kleine Scheidegg": -42,
    "Lauterbrunnen": -42,
    "Mürren": -52,
    "Blüemlisalp Hut": -70,
    "Hohtürli Pass": -42,
    "Kandersteg": -42,
}

ns = f"{{{SVG_NS}}}"
for i, circle in enumerate(circles[: len(landmarks)]):
    parent_elem = parent_map.get(circle)
    if parent_elem is None:
        continue

    cx, cy = float(circle.get("cx", "0")), float(circle.get("cy", "0"))
    lm = landmarks[i]
    lm_color = TYPE_COLORS.get(lm["type"], "#c45a00")
    y_off = label_offsets.get(lm["name"], -42)

    # Text anchor based on position
    if i == 0:
        anchor, dx = "start", 10
    elif i == len(landmarks) - 1:
        anchor, dx = "end", -10
    else:
        anchor, dx = "middle", 0

    # Vertical dashed marker line
    vline = ET.SubElement(parent_elem, f"{ns}line")
    for attr, val in [("x1", cx), ("y1", cy), ("x2", cx), ("y2", plot_bottom_y)]:
        vline.set(attr, f"{val:.1f}")
    vline.set("stroke", lm_color)
    vline.set("stroke-width", "2")
    vline.set("stroke-dasharray", "8,5")
    vline.set("opacity", "0.55")

    # Landmark name (bold, colored by type)
    name_el = ET.SubElement(parent_elem, f"{ns}text")
    name_el.set("x", f"{cx + dx:.1f}")
    name_el.set("y", f"{cy + y_off:.1f}")
    name_el.set("text-anchor", anchor)
    name_el.set("font-size", "32")
    name_el.set("font-family", "DejaVu Sans, Helvetica, Arial, sans-serif")
    name_el.set("fill", lm_color)
    name_el.set("font-weight", "bold")
    name_el.text = lm["name"]

    # Elevation label (gray, below name)
    elev_el = ET.SubElement(parent_elem, f"{ns}text")
    elev_el.set("x", f"{cx + dx:.1f}")
    elev_el.set("y", f"{cy + y_off + 24:.1f}")
    elev_el.set("text-anchor", anchor)
    elev_el.set("font-size", "26")
    elev_el.set("font-family", "DejaVu Sans, Helvetica, Arial, sans-serif")
    elev_el.set("fill", "#555555")
    elev_el.text = f"{lm['elev']:.0f} m"

# Add vertical exaggeration note (spec requirement) - positioned bottom-right
note_el = ET.SubElement(root, f"{ns}text")
note_el.set("x", "4650")
note_el.set("y", f"{plot_bottom_y + 48:.0f}")
note_el.set("text-anchor", "end")
note_el.set("font-size", "28")
note_el.set("font-family", "DejaVu Sans, Helvetica, Arial, sans-serif")
note_el.set("fill", "#555555")
note_el.set("font-style", "italic")
note_el.text = "Vertical exaggeration ~10\u00d7 for terrain visibility"

# Convert to PNG
cairosvg.svg2png(bytestring=ET.tostring(root, encoding="unicode").encode("utf-8"), write_to="plot.png")
