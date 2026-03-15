""" pyplots.ai
stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 68/100 | Created: 2026-03-15
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Field measurements from a geological mapping campaign
np.random.seed(42)

# Bedding planes - consistent NE strike (~040°), moderate SE dip (~30°)
n_bedding = 25
bedding_strike = np.random.normal(40, 8, n_bedding) % 360
bedding_dip = np.clip(np.random.normal(30, 5, n_bedding), 5, 85)

# Fault planes - steeper, striking ESE (~120°), steep dip (~65°)
n_faults = 15
fault_strike = np.random.normal(120, 12, n_faults) % 360
fault_dip = np.clip(np.random.normal(65, 8, n_faults), 10, 89)

# Joint set - sub-vertical (~80°), striking roughly N-S (~350°)
n_joints = 20
joint_strike = np.random.normal(350, 10, n_joints) % 360
joint_dip = np.clip(np.random.normal(80, 6, n_joints), 15, 89)

# Equal-area (Schmidt net) lower-hemisphere projection
# Pole to plane: trend = strike + 90°, plunge = 90° - dip
# Projection radius: r = √2 · sin(dip_rad / 2)
# Cartesian: x = r · sin(trend_rad), y = r · cos(trend_rad)

# Primitive circle (outer boundary representing the horizontal plane)
theta_circle = np.linspace(0, 2 * np.pi, 361)
circle_points = [(round(float(np.sin(t)), 4), round(float(np.cos(t)), 4)) for t in theta_circle]

# Tick marks every 10° around perimeter
tick_points = []
for deg in range(0, 360, 10):
    rad = np.radians(deg)
    inner, outer = 0.97, 1.03
    tick_points.append((round(inner * np.sin(rad), 4), round(inner * np.cos(rad), 4)))
    tick_points.append((round(outer * np.sin(rad), 4), round(outer * np.cos(rad), 4)))
    tick_points.append(None)

# Compass markers (N, E, S, W as small cross marks beyond the circle)
compass_points = []
for _bearing, offset_x, offset_y in [(0, 0, 1.12), (90, 1.12, 0), (180, 0, -1.12), (270, -1.12, 0)]:
    compass_points.append((round(offset_x - 0.02, 4), round(offset_y, 4)))
    compass_points.append((round(offset_x + 0.02, 4), round(offset_y, 4)))
    compass_points.append(None)
    compass_points.append((round(offset_x, 4), round(offset_y - 0.02, 4)))
    compass_points.append((round(offset_x, 4), round(offset_y + 0.02, 4)))
    compass_points.append(None)

# Great circle computation for all planes
# For rake angle α (0 to π), a line in the plane has:
#   plunge = arcsin(sin(dip) · sin(α))
#   trend = strike + atan2(sin(α) · cos(dip), cos(α))
alphas = np.linspace(0, np.pi, 91)

feature_sets = [
    ("Bedding", bedding_strike, bedding_dip),
    ("Faults", fault_strike, fault_dip),
    ("Joints", joint_strike, joint_dip),
]

gc_series = {}
pole_series = {}

for name, strikes, dips in feature_sets:
    # Great circles with None separators between each plane
    gc_data = []
    for i in range(len(strikes)):
        d_rad = np.radians(dips[i])
        plunges = np.degrees(np.arcsin(np.sin(d_rad) * np.sin(alphas)))
        trends = strikes[i] + np.degrees(np.arctan2(np.sin(alphas) * np.cos(d_rad), np.cos(alphas)))
        r = np.sqrt(2) * np.sin(np.radians((90 - plunges) / 2))
        x = r * np.sin(np.radians(trends))
        y = r * np.cos(np.radians(trends))
        if gc_data:
            gc_data.append(None)
        gc_data.extend([(round(float(xi), 4), round(float(yi), 4)) for xi, yi in zip(x, y, strict=True)])
    gc_series[name] = gc_data

    # Poles to planes
    pole_trend_rad = np.radians((strikes + 90) % 360)
    pole_r = np.sqrt(2) * np.sin(np.radians(dips / 2))
    pole_x = pole_r * np.sin(pole_trend_rad)
    pole_y = pole_r * np.cos(pole_trend_rad)
    pole_series[name] = [(round(float(xi), 4), round(float(yi), 4)) for xi, yi in zip(pole_x, pole_y, strict=True)]

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#eeeeee",
    colors=(
        "#aaaaaa",  # primitive circle
        "#aaaaaa",  # tick marks
        "#aaaaaa",  # compass marks
        "#306998",  # bedding great circles
        "#D4513D",  # fault great circles
        "#2CA02C",  # joint great circles
        "#306998",  # bedding poles
        "#D4513D",  # fault poles
        "#2CA02C",  # joint poles
    ),
    title_font_size=56,
    label_font_size=1,
    major_label_font_size=1,
    legend_font_size=36,
    value_font_size=20,
    tooltip_font_size=28,
    opacity=0.5,
    opacity_hover=0.8,
)

# Chart
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="stereonet-equal-area · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    xrange=(-1.35, 1.35),
    range=(-1.35, 1.35),
    dots_size=0,
    allow_interruptions=True,
    margin_top=40,
    margin_bottom=60,
    margin_left=20,
    margin_right=20,
)

# Structural elements (circle, ticks, compass)
chart.add("", circle_points, stroke=True, show_dots=False, stroke_style={"width": 2.5})
chart.add("", tick_points, stroke=True, show_dots=False, stroke_style={"width": 1.5})
chart.add("", compass_points, stroke=True, show_dots=False, stroke_style={"width": 2})

# Great circles (planes)
chart.add("Bedding (planes)", gc_series["Bedding"], stroke=True, show_dots=False, stroke_style={"width": 1.5})
chart.add("Faults (planes)", gc_series["Faults"], stroke=True, show_dots=False, stroke_style={"width": 1.5})
chart.add("Joints (planes)", gc_series["Joints"], stroke=True, show_dots=False, stroke_style={"width": 1.5})

# Poles to planes (scatter points)
chart.add("Bedding (poles)", pole_series["Bedding"], stroke=False, show_dots=True, dots_size=12)
chart.add("Fault (poles)", pole_series["Faults"], stroke=False, show_dots=True, dots_size=12)
chart.add("Joint (poles)", pole_series["Joints"], stroke=False, show_dots=True, dots_size=12)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
