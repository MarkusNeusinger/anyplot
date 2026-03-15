""" pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: pygal 3.1.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-15
"""

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

# Landmarks along the trail
landmarks = [
    {"name": "Grindelwald", "km": 0, "note": "Start"},
    {"name": "Kleine Scheidegg", "km": 22, "note": "Pass"},
    {"name": "Lauterbrunnen Valley", "km": 38, "note": "Valley"},
    {"name": "Mürren", "km": 55, "note": "Summit Viewpoint"},
    {"name": "Blüemlisalp Hut", "km": 72, "note": "Mountain Hut"},
    {"name": "Hohtürli Pass", "km": 85, "note": "High Pass"},
    {"name": "Kandersteg", "km": 120, "note": "End"},
]

# Get elevation at landmark positions
for lm in landmarks:
    idx = np.argmin(np.abs(distances_km - lm["km"]))
    lm["elev"] = float(elevation_m[idx])

# Custom style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2d2d2d",
    foreground_strong="#2d2d2d",
    foreground_subtle="#e0e0e0",
    colors=("#306998", "#c45a00", "#0e7c6b", "#7b2d8e", "#cc3333", "#2277aa", "#e6960d"),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=52,
    label_font_size=36,
    major_label_font_size=34,
    value_font_size=28,
    legend_font_size=32,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    major_label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    opacity=0.50,
    opacity_hover=0.65,
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="3,3",
    major_guide_stroke_color="#cccccc",
    major_guide_stroke_dasharray="6,3",
    stroke_opacity=1.0,
    stroke_opacity_hover=1.0,
    tooltip_font_size=26,
    tooltip_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    tooltip_border_radius=8,
)

# Chart
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
    legend_box_size=26,
    value_formatter=lambda x: f"{x:,.0f} m",
    x_value_formatter=lambda x: f"{x:.0f} km",
    interpolate="cubic",
    interpolation_precision=300,
    min_scale=5,
    max_scale=10,
    margin_bottom=120,
    margin_left=100,
    margin_right=60,
    margin_top=60,
    spacing=12,
    tooltip_fancy_mode=True,
    range=(600, 2200),
    xrange=(0, 125),
)

# Elevation profile as filled XY series
profile_data = [
    {"value": (float(d), float(e)), "label": f"{d:.1f} km — {e:.0f} m"} for d, e in zip(distances_km, elevation_m, strict=True)
]
chart.add("Elevation Profile", profile_data)

# Landmark markers as separate series
landmark_data = [
    {"value": (float(lm["km"]), lm["elev"]), "label": f"{lm['name']} ({lm['note']}) — {lm['elev']:.0f} m"}
    for lm in landmarks
]
chart.add("Landmarks", landmark_data, fill=False, show_dots=True, dots_size=14, stroke=False)

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
