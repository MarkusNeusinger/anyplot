""" pyplots.ai
stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-15
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


def clip_to_circle(x, y):
    """Clip point to be within the primitive circle (r <= 1)."""
    r = np.sqrt(x**2 + y**2)
    if r > 1.0:
        x, y = x / r, y / r
    return x, y


# Primitive circle + tick marks + N label combined as one series
structural_points = []

# Primitive circle (outer boundary)
theta_circle = np.linspace(0, 2 * np.pi, 361)
for t in theta_circle:
    structural_points.append((round(float(np.sin(t)), 4), round(float(np.cos(t)), 4)))
structural_points.append(None)

# Tick marks every 10° around perimeter
for deg in range(0, 360, 10):
    rad = np.radians(deg)
    inner, outer = 0.96, 1.04
    structural_points.append((round(inner * np.sin(rad), 4), round(inner * np.cos(rad), 4)))
    structural_points.append((round(outer * np.sin(rad), 4), round(outer * np.cos(rad), 4)))
    structural_points.append(None)

# N label at top - letter shape using connected line segments
n_cx, n_cy = 0.0, 1.14
n_s = 0.035
for t in np.linspace(0, 1, 10):
    structural_points.append((round(n_cx - n_s, 4), round(n_cy - n_s * 2.5 + t * n_s * 5, 4)))
structural_points.append(None)
for t in np.linspace(0, 1, 10):
    structural_points.append((round(n_cx - n_s + t * n_s * 2, 4), round(n_cy + n_s * 2.5 - t * n_s * 5, 4)))
structural_points.append(None)
for t in np.linspace(0, 1, 10):
    structural_points.append((round(n_cx + n_s, 4), round(n_cy - n_s * 2.5 + t * n_s * 5, 4)))

# Equal-area net grid lines (subtle, as spec requires)
grid_points = []
# Small circles at dip intervals of 30° (at 30°, 60°)
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


# Great circle computation for all planes
alphas = np.linspace(0, np.pi, 91)

feature_sets = [
    ("Bedding", bedding_strike, bedding_dip),
    ("Faults", fault_strike, fault_dip),
    ("Joints", joint_strike, joint_dip),
]

# Visual hierarchy: bedding is primary feature (thickest), faults secondary, joints tertiary
gc_widths = {"Bedding": 3.0, "Faults": 2.2, "Joints": 1.8}
pole_sizes = {"Bedding": 16, "Faults": 12, "Joints": 10}

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
        for xi, yi in zip(x, y, strict=True):
            cx, cy = clip_to_circle(float(xi), float(yi))
            gc_data.append((round(cx, 4), round(cy, 4)))
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
all_pole_x = np.array(all_pole_x)
all_pole_y = np.array(all_pole_y)

grid_res = 80
gx = np.linspace(-1, 1, grid_res)
gy = np.linspace(-1, 1, grid_res)
gxx, gyy = np.meshgrid(gx, gy)
dx = gx[1] - gx[0]

# Gaussian kernel density on projected coordinates
sigma = 0.12
density = np.zeros_like(gxx)
for px, py in zip(all_pole_x, all_pole_y, strict=True):
    density += np.exp(-((gxx - px) ** 2 + (gyy - py) ** 2) / (2 * sigma**2))

# Mask outside the primitive circle
mask = gxx**2 + gyy**2 > 1.0
density[mask] = 0


def trace_contour(density, gx, gy, level):
    """Trace contour lines using marching squares with proper edge following."""
    ny, nx = density.shape
    segments = []

    # Find all cell edge crossings and build segments
    for j in range(ny - 1):
        for i in range(nx - 1):
            # Four corners of cell: TL, TR, BR, BL
            vals = [density[j, i], density[j, i + 1], density[j + 1, i + 1], density[j + 1, i]]
            above = [v >= level for v in vals]
            case = above[0] * 8 + above[1] * 4 + above[2] * 2 + above[3] * 1

            if case == 0 or case == 15:
                continue

            # Interpolation along edges
            def interp_edge(v0, v1, p0, p1):
                if abs(v1 - v0) < 1e-12:
                    t = 0.5
                else:
                    t = (level - v0) / (v1 - v0)
                return (p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1]))

            corners = [(gx[i], gy[j]), (gx[i + 1], gy[j]), (gx[i + 1], gy[j + 1]), (gx[i], gy[j + 1])]

            edges = {}
            # Top edge (0-1)
            if above[0] != above[1]:
                edges["top"] = interp_edge(vals[0], vals[1], corners[0], corners[1])
            # Right edge (1-2)
            if above[1] != above[2]:
                edges["right"] = interp_edge(vals[1], vals[2], corners[1], corners[2])
            # Bottom edge (2-3)
            if above[2] != above[3]:
                edges["bottom"] = interp_edge(vals[2], vals[3], corners[2], corners[3])
            # Left edge (3-0)
            if above[3] != above[0]:
                edges["left"] = interp_edge(vals[3], vals[0], corners[3], corners[0])

            edge_keys = list(edges.keys())
            if len(edge_keys) == 2:
                p0, p1 = edges[edge_keys[0]], edges[edge_keys[1]]
                if p0[0] ** 2 + p0[1] ** 2 <= 1.02 and p1[0] ** 2 + p1[1] ** 2 <= 1.02:
                    segments.append((p0, p1))
            elif len(edge_keys) == 4:
                # Saddle point - connect based on center value
                center = sum(vals) / 4
                if center >= level:
                    pairs = [("top", "right"), ("bottom", "left")]
                else:
                    pairs = [("top", "left"), ("bottom", "right")]
                for k0, k1 in pairs:
                    p0, p1 = edges[k0], edges[k1]
                    if p0[0] ** 2 + p0[1] ** 2 <= 1.02 and p1[0] ** 2 + p1[1] ** 2 <= 1.02:
                        segments.append((p0, p1))

    # Chain segments into polylines
    if not segments:
        return []

    polylines = []
    used = [False] * len(segments)
    eps = dx * 1.5

    for start_idx in range(len(segments)):
        if used[start_idx]:
            continue
        used[start_idx] = True
        chain = [segments[start_idx][0], segments[start_idx][1]]

        # Extend forward
        changed = True
        while changed:
            changed = False
            for k in range(len(segments)):
                if used[k]:
                    continue
                s = segments[k]
                d0 = (chain[-1][0] - s[0][0]) ** 2 + (chain[-1][1] - s[0][1]) ** 2
                d1 = (chain[-1][0] - s[1][0]) ** 2 + (chain[-1][1] - s[1][1]) ** 2
                if d0 < eps**2:
                    chain.append(s[1])
                    used[k] = True
                    changed = True
                    break
                elif d1 < eps**2:
                    chain.append(s[0])
                    used[k] = True
                    changed = True
                    break

        # Extend backward
        changed = True
        while changed:
            changed = False
            for k in range(len(segments)):
                if used[k]:
                    continue
                s = segments[k]
                d0 = (chain[0][0] - s[0][0]) ** 2 + (chain[0][1] - s[0][1]) ** 2
                d1 = (chain[0][0] - s[1][0]) ** 2 + (chain[0][1] - s[1][1]) ** 2
                if d0 < eps**2:
                    chain.insert(0, s[1])
                    used[k] = True
                    changed = True
                    break
                elif d1 < eps**2:
                    chain.insert(0, s[0])
                    used[k] = True
                    changed = True
                    break

        if len(chain) >= 3:
            polylines.append(chain)

    return polylines


# Extract contour polylines at density levels
contour_levels = [2.0, 4.0, 6.0, 8.0]
max_density = density.max()
all_contour_points = []

for level in contour_levels:
    if level >= max_density:
        continue
    polylines = trace_contour(density, gx, gy, level)
    for polyline in polylines:
        if all_contour_points:
            all_contour_points.append(None)
        for pt in polyline:
            cx, cy = clip_to_circle(pt[0], pt[1])
            all_contour_points.append((round(cx, 4), round(cy, 4)))


# Style - colorblind-safe palette (blue, red, amber)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#eeeeee",
    colors=(
        "#306998",  # bedding great circles (blue - primary)
        "#D4513D",  # fault great circles (red)
        "#DAA520",  # joint great circles (amber/gold)
        "#306998",  # bedding poles
        "#D4513D",  # fault poles
        "#DAA520",  # joint poles
        "#888888",  # density contours
        "#bbbbbb",  # grid lines
        "#555555",  # stereonet boundary
    ),
    title_font_size=56,
    label_font_size=1,
    major_label_font_size=1,
    legend_font_size=36,
    value_font_size=20,
    tooltip_font_size=28,
    opacity=0.7,
    opacity_hover=0.9,
)

# Chart
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="stereonet-equal-area \u00b7 pygal \u00b7 pyplots.ai",
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

# Great circles (planes) - visual hierarchy via line weight
chart.add(
    "Bedding (planes)", gc_series["Bedding"], stroke=True, show_dots=False, stroke_style={"width": gc_widths["Bedding"]}
)
chart.add(
    "Faults (planes)", gc_series["Faults"], stroke=True, show_dots=False, stroke_style={"width": gc_widths["Faults"]}
)
chart.add(
    "Joints (planes)", gc_series["Joints"], stroke=True, show_dots=False, stroke_style={"width": gc_widths["Joints"]}
)

# Poles to planes (scatter points) - visual hierarchy via dot size
chart.add("Bedding (poles)", pole_series["Bedding"], stroke=False, show_dots=True, dots_size=pole_sizes["Bedding"])
chart.add("Faults (poles)", pole_series["Faults"], stroke=False, show_dots=True, dots_size=pole_sizes["Faults"])
chart.add("Joints (poles)", pole_series["Joints"], stroke=False, show_dots=True, dots_size=pole_sizes["Joints"])

# Density contours - single combined series
if all_contour_points:
    chart.add(
        "Density contours",
        all_contour_points,
        stroke=True,
        show_dots=False,
        stroke_style={"width": 1.8, "dasharray": "6,3"},
    )

# Grid lines (subtle equal-area net) - named to avoid orphan legend entry
chart.add("Grid", grid_points, stroke=True, show_dots=False, stroke_style={"width": 0.8, "dasharray": "4,4"})

# Stereonet boundary: primitive circle + tick marks + N label
chart.add("Stereonet", structural_points, stroke=True, show_dots=False, stroke_style={"width": 2.5})

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
