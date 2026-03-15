""" pyplots.ai
stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 70/100 | Created: 2026-03-15
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
# Projection radius: r = √2 · sin(plunge_rad / 2) where plunge = 90 - dip for poles
# For great circles: r = √2 · sin((90 - plunge_of_line) / 2)
# Cartesian: x = r · sin(trend_rad), y = r · cos(trend_rad)

# Primitive circle (outer boundary)
theta_circle = np.linspace(0, 2 * np.pi, 361)
circle_points = [(round(float(np.sin(t)), 4), round(float(np.cos(t)), 4)) for t in theta_circle]

# Tick marks every 10° around perimeter
tick_points = []
for deg in range(0, 360, 10):
    rad = np.radians(deg)
    inner, outer = 0.96, 1.04
    tick_points.append((round(inner * np.sin(rad), 4), round(inner * np.cos(rad), 4)))
    tick_points.append((round(outer * np.sin(rad), 4), round(outer * np.cos(rad), 4)))
    tick_points.append(None)

# Equal-area net grid lines (subtle, as spec requires)
# Small circles at dip intervals of 30° (at 30°, 60°)
grid_points = []
for dip_grid in [30, 60]:
    r_grid = np.sqrt(2) * np.sin(np.radians(dip_grid / 2))
    theta_grid = np.linspace(0, 2 * np.pi, 181)
    for t in theta_grid:
        grid_points.append((round(float(r_grid * np.sin(t)), 4), round(float(r_grid * np.cos(t)), 4)))
    grid_points.append(None)

# Diametral lines every 30° (great circle diameters through center)
for az in range(0, 180, 30):
    rad = np.radians(az)
    grid_points.append((round(-np.sin(rad), 4), round(-np.cos(rad), 4)))
    grid_points.append((round(np.sin(rad), 4), round(np.cos(rad), 4)))
    grid_points.append(None)

# Compass direction labels as dot patterns
# N label at top - letter shape using connected line segments
n_label = []
n_cx, n_cy = 0.0, 1.15
n_s = 0.03
for t in np.linspace(0, 1, 10):
    n_label.append((round(n_cx - n_s, 4), round(n_cy - n_s * 2 + t * n_s * 4, 4)))
n_label.append(None)
for t in np.linspace(0, 1, 10):
    n_label.append((round(n_cx - n_s + t * n_s * 2, 4), round(n_cy + n_s * 2 - t * n_s * 4, 4)))
n_label.append(None)
for t in np.linspace(0, 1, 10):
    n_label.append((round(n_cx + n_s, 4), round(n_cy - n_s * 2 + t * n_s * 4, 4)))


# Great circle computation for all planes
alphas = np.linspace(0, np.pi, 91)

feature_sets = [
    ("Bedding", bedding_strike, bedding_dip),
    ("Faults", fault_strike, fault_dip),
    ("Joints", joint_strike, joint_dip),
]

gc_series = {}
pole_series = {}
all_pole_x = []
all_pole_y = []

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
    all_pole_x.extend(pole_x)
    all_pole_y.extend(pole_y)

# Kamb density contours on all pole data
# Grid-based density estimation in projected space
all_pole_x = np.array(all_pole_x)
all_pole_y = np.array(all_pole_y)

grid_res = 60
gx = np.linspace(-1, 1, grid_res)
gy = np.linspace(-1, 1, grid_res)
gxx, gyy = np.meshgrid(gx, gy)

# Gaussian kernel density on projected coordinates
sigma = 0.12
density = np.zeros_like(gxx)
for px, py in zip(all_pole_x, all_pole_y, strict=True):
    density += np.exp(-((gxx - px) ** 2 + (gyy - py) ** 2) / (2 * sigma**2))

# Mask outside the primitive circle
mask = gxx**2 + gyy**2 > 1.0
density[mask] = 0

# Extract contour lines using a simple marching approach
# Generate contour polylines at specific density levels
contour_levels = [2.0, 4.0, 6.0, 8.0]
max_density = density.max()
contour_series = []

for level in contour_levels:
    if level >= max_density:
        continue
    level_points = []
    # Scan horizontal edges for contour crossings
    for i in range(grid_res - 1):
        for j in range(grid_res):
            v0, v1 = density[j, i], density[j, i + 1]
            if (v0 - level) * (v1 - level) < 0 and v0 != v1:
                frac = (level - v0) / (v1 - v0)
                cx = gx[i] + frac * (gx[i + 1] - gx[i])
                cy = gy[j]
                if cx**2 + cy**2 <= 1.0:
                    level_points.append((cx, cy))
    # Scan vertical edges
    for i in range(grid_res):
        for j in range(grid_res - 1):
            v0, v1 = density[j, i], density[j + 1, i]
            if (v0 - level) * (v1 - level) < 0 and v0 != v1:
                frac = (level - v0) / (v1 - v0)
                cx = gx[i]
                cy = gy[j] + frac * (gy[j + 1] - gy[j])
                if cx**2 + cy**2 <= 1.0:
                    level_points.append((cx, cy))

    if level_points:
        # Sort points by angle from each cluster centroid to form connected contours
        pts = np.array(level_points)
        # Order points by angle for smoother contour rendering
        angles = np.arctan2(pts[:, 0], pts[:, 1])
        order = np.argsort(angles)
        sorted_pts = pts[order]
        # Split into segments when consecutive points are far apart
        segment = [(round(float(sorted_pts[0, 0]), 4), round(float(sorted_pts[0, 1]), 4))]
        for k in range(1, len(sorted_pts)):
            dist = np.sqrt(
                (sorted_pts[k, 0] - sorted_pts[k - 1, 0]) ** 2 + (sorted_pts[k, 1] - sorted_pts[k - 1, 1]) ** 2
            )
            if dist > 0.15:
                segment.append(None)
            segment.append((round(float(sorted_pts[k, 0]), 4), round(float(sorted_pts[k, 1]), 4)))
        contour_series.append(segment)


# Style - colorblind-safe palette (blue, orange, amber instead of green)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#eeeeee",
    colors=(
        "#d0d0d0",  # grid lines
        "#777777",  # structural elements (circle + ticks + N)
        "#306998",  # bedding great circles
        "#D4513D",  # fault great circles
        "#DAA520",  # joint great circles (amber/gold, colorblind-safe)
        "#306998",  # bedding poles
        "#D4513D",  # fault poles
        "#DAA520",  # joint poles (amber/gold)
        "#666666",  # contour level 1
        "#555555",  # contour level 2
        "#444444",  # contour level 3
        "#333333",  # contour level 4
    ),
    title_font_size=56,
    label_font_size=1,
    major_label_font_size=1,
    legend_font_size=36,
    value_font_size=20,
    tooltip_font_size=28,
    opacity=0.6,
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
    legend_at_bottom_columns=4,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    xrange=(-1.25, 1.25),
    range=(-1.25, 1.25),
    dots_size=0,
    allow_interruptions=True,
    margin_top=30,
    margin_bottom=50,
    margin_left=10,
    margin_right=10,
)

# Grid lines (subtle equal-area net)
chart.add("", grid_points, stroke=True, show_dots=False, stroke_style={"width": 0.8, "dasharray": "4,4"})

# Combine structural elements: circle + ticks + N label
structural = circle_points + [None] + tick_points + [None] + n_label
chart.add("", structural, stroke=True, show_dots=False, stroke_style={"width": 2.5})

# Great circles (planes) - thicker lines for visibility
chart.add("Bedding (planes)", gc_series["Bedding"], stroke=True, show_dots=False, stroke_style={"width": 2.5})
chart.add("Faults (planes)", gc_series["Faults"], stroke=True, show_dots=False, stroke_style={"width": 2.5})
chart.add("Joints (planes)", gc_series["Joints"], stroke=True, show_dots=False, stroke_style={"width": 2.5})

# Poles to planes (scatter points)
chart.add("Bedding (poles)", pole_series["Bedding"], stroke=False, show_dots=True, dots_size=14)
chart.add("Faults (poles)", pole_series["Faults"], stroke=False, show_dots=True, dots_size=14)
chart.add("Joints (poles)", pole_series["Joints"], stroke=False, show_dots=True, dots_size=14)

# Density contours - only first gets legend label
for i, contour_data in enumerate(contour_series):
    label = "Density contours" if i == 0 else ""
    chart.add(label, contour_data, stroke=True, show_dots=False, stroke_style={"width": 1.5, "dasharray": "6,3"})

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
