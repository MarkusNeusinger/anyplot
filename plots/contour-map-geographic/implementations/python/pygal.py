""" pyplots.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: pygal 3.1.0 | Python 3.13.11
Quality: 85/100 | Created: 2026-01-17
"""

import sys
from pathlib import Path


# Remove current directory from path to avoid shadowing pygal module
sys.path = [p for p in sys.path if p != str(Path(__file__).parent)]

import cairosvg  # noqa: E402
import numpy as np  # noqa: E402
import pygal as pygal_lib  # noqa: E402
from pygal.style import Style  # noqa: E402


# Data - Generate synthetic temperature data over a geographic grid
np.random.seed(42)

# Define geographic bounds (roughly Europe/Atlantic region)
lon_min, lon_max = -30, 50
lat_min, lat_max = 25, 70

# Create regular grid for contour data
n_grid = 40
lon_grid = np.linspace(lon_min, lon_max, n_grid)
lat_grid = np.linspace(lat_min, lat_max, n_grid)
LON, LAT = np.meshgrid(lon_grid, lat_grid)

# Generate synthetic temperature field (°C)
temp_base = 25 - (LAT - lat_min) * 0.3
temp_base += (LON - lon_min) * 0.08

# High pressure center (warm)
high_lon, high_lat = 15, 50
dist_high = np.sqrt((LON - high_lon) ** 2 + (LAT - high_lat) ** 2)
temp_anomaly1 = 8 * np.exp(-(dist_high**2) / 300)

# Low pressure center (cold)
low_lon, low_lat = -10, 60
dist_low = np.sqrt((LON - low_lon) ** 2 + (LAT - low_lat) ** 2)
temp_anomaly2 = -10 * np.exp(-(dist_low**2) / 250)

# Warm anomaly in Mediterranean
med_lon, med_lat = 25, 35
dist_med = np.sqrt((LON - med_lon) ** 2 + (LAT - med_lat) ** 2)
temp_anomaly3 = 6 * np.exp(-(dist_med**2) / 200)

TEMP = temp_base + temp_anomaly1 + temp_anomaly2 + temp_anomaly3
TEMP += np.random.normal(0, 0.5, TEMP.shape)

contour_levels = np.arange(-4, 26, 4)

# Simplified coastlines for Europe/Atlantic (lon, lat format)
coastlines = [
    [(-10, 50), (-5, 55), (-7, 58), (-2, 59), (0, 61), (2, 57), (-5, 50), (-10, 50)],
    [(-10, 36), (-9, 43), (-2, 43), (4, 42), (-6, 36), (-10, 36)],
    [(-5, 48), (2, 51), (4, 51), (10, 54), (4, 56), (-2, 53), (-5, 48)],
    [(5, 58), (11, 58), (18, 63), (25, 70), (30, 70), (25, 62), (10, 56), (5, 58)],
    [(8, 44), (18, 40), (12, 38), (8, 44)],
    [(-10, 30), (10, 32), (30, 31), (35, 32), (35, 28), (10, 28), (-10, 30)],
    [(20, 35), (30, 37), (36, 35), (27, 35), (20, 35)],
]

# Color scale for temperature (blue cold -> red warm)
temp_colors = [
    "#2166ac",  # -4: Deep blue
    "#4393c3",  # 0: Blue
    "#92c5de",  # 4: Light blue
    "#d1e5f0",  # 8: Very light blue
    "#fddbc7",  # 12: Light orange
    "#f4a582",  # 16: Orange
    "#d6604d",  # 20: Red-orange
    "#b2182b",  # 24: Red
]

# Custom style for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="#C8DDF0",
    foreground="#333333",
    foreground_strong="#111111",
    foreground_subtle="#666666",
    guide_stroke_color="rgba(100, 100, 100, 0.25)",
    guide_stroke_dasharray="",
    colors=("#666666",) * len(coastlines),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=44,
    value_font_size=36,
)

# Create base XY chart
chart = pygal_lib.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="contour-map-geographic · pygal · pyplots.ai",
    x_title="Longitude (°E)",
    y_title="Latitude (°N)",
    show_legend=False,
    stroke=True,
    dots_size=0,
    show_x_guides=True,
    show_y_guides=True,
    explicit_size=True,
    print_values=False,
    xrange=(lon_min, lon_max),
    range=(lat_min, lat_max),
    margin=120,
    margin_top=200,
    margin_bottom=200,
    margin_left=280,
    margin_right=300,
)

# Add coastlines as background
for coords in coastlines:
    chart.add(None, coords, stroke=True, dots_size=0, show_dots=False, fill=False)

# Plot dimensions
plot_x = 280
plot_y = 200
plot_width = 4800 - 280 - 300
plot_height = 2700 - 200 - 200

# Build custom SVG content for contours
svg_parts = []

# Draw filled contours (background)
cell_w = plot_width / (n_grid - 1)
cell_h = plot_height / (n_grid - 1)

for i in range(n_grid - 1):
    for j in range(n_grid - 1):
        avg_temp = (TEMP[i, j] + TEMP[i, j + 1] + TEMP[i + 1, j] + TEMP[i + 1, j + 1]) / 4
        color_idx = int((avg_temp + 4) / 4)
        color_idx = max(0, min(color_idx, len(temp_colors) - 1))
        color = temp_colors[color_idx]
        px = plot_x + (lon_grid[j] - lon_min) / (lon_max - lon_min) * plot_width
        py = plot_y + plot_height - (lat_grid[i + 1] - lat_min) / (lat_max - lat_min) * plot_height
        svg_parts.append(
            f'<rect x="{px:.1f}" y="{py:.1f}" width="{cell_w + 1:.1f}" '
            f'height="{cell_h + 1:.1f}" fill="{color}" fill-opacity="0.6" stroke="none"/>'
        )

# Draw contour lines using marching squares algorithm with path connection
for level in contour_levels:
    line_color = "#333333"
    line_width = 3 if level % 8 == 0 else 2

    # Collect all segments for this level
    all_segments = []

    for i in range(n_grid - 1):
        for j in range(n_grid - 1):
            z00, z01 = TEMP[i, j], TEMP[i, j + 1]
            z10, z11 = TEMP[i + 1, j], TEMP[i + 1, j + 1]

            case = 0
            if z00 >= level:
                case |= 1
            if z01 >= level:
                case |= 2
            if z11 >= level:
                case |= 4
            if z10 >= level:
                case |= 8

            if case == 0 or case == 15:
                continue

            # Cell corner pixel coordinates
            x0 = plot_x + (lon_grid[j] - lon_min) / (lon_max - lon_min) * plot_width
            y0 = plot_y + plot_height - (lat_grid[i + 1] - lat_min) / (lat_max - lat_min) * plot_height
            x1 = plot_x + (lon_grid[j + 1] - lon_min) / (lon_max - lon_min) * plot_width
            y1 = plot_y + plot_height - (lat_grid[i] - lat_min) / (lat_max - lat_min) * plot_height

            # Linear interpolation (inline)
            t_left = 0.5 if abs(z10 - z00) < 1e-10 else (level - z00) / (z10 - z00)
            t_right = 0.5 if abs(z11 - z01) < 1e-10 else (level - z01) / (z11 - z01)
            t_top = 0.5 if abs(z11 - z10) < 1e-10 else (level - z10) / (z11 - z10)
            t_bottom = 0.5 if abs(z01 - z00) < 1e-10 else (level - z00) / (z01 - z00)

            left = (x0, y0 - cell_h * t_left)
            right = (x1, y1 + cell_h * t_right)
            top = (x0 + cell_w * t_top, y0 - cell_h)
            bottom = (x0 + cell_w * t_bottom, y0)

            if case in [1, 14]:
                all_segments.append((left, bottom))
            elif case in [2, 13]:
                all_segments.append((bottom, right))
            elif case in [3, 12]:
                all_segments.append((left, right))
            elif case in [4, 11]:
                all_segments.append((right, top))
            elif case == 5:
                all_segments.append((left, top))
                all_segments.append((bottom, right))
            elif case in [6, 9]:
                all_segments.append((bottom, top))
            elif case in [7, 8]:
                all_segments.append((left, top))
            elif case == 10:
                all_segments.append((left, bottom))
                all_segments.append((right, top))

    # Connect segments into polylines for smoother rendering
    tolerance = 1.5
    polylines = []
    used = [False] * len(all_segments)

    for idx, seg in enumerate(all_segments):
        if used[idx]:
            continue
        used[idx] = True
        chain = list(seg)

        # Try extending the chain from both ends
        extended = True
        while extended:
            extended = False
            for j, other in enumerate(all_segments):
                if used[j]:
                    continue
                p0, p1 = other
                # Check if other connects to end of chain
                if abs(chain[-1][0] - p0[0]) < tolerance and abs(chain[-1][1] - p0[1]) < tolerance:
                    chain.append(p1)
                    used[j] = True
                    extended = True
                elif abs(chain[-1][0] - p1[0]) < tolerance and abs(chain[-1][1] - p1[1]) < tolerance:
                    chain.append(p0)
                    used[j] = True
                    extended = True
                # Check if other connects to start of chain
                elif abs(chain[0][0] - p1[0]) < tolerance and abs(chain[0][1] - p1[1]) < tolerance:
                    chain.insert(0, p0)
                    used[j] = True
                    extended = True
                elif abs(chain[0][0] - p0[0]) < tolerance and abs(chain[0][1] - p0[1]) < tolerance:
                    chain.insert(0, p1)
                    used[j] = True
                    extended = True

        polylines.append(chain)

    # Render polylines as SVG paths
    for chain in polylines:
        if len(chain) < 2:
            continue
        path_data = f"M {chain[0][0]:.1f} {chain[0][1]:.1f}"
        for pt in chain[1:]:
            path_data += f" L {pt[0]:.1f} {pt[1]:.1f}"
        svg_parts.append(
            f'<path d="{path_data}" fill="none" stroke="{line_color}" '
            f'stroke-width="{line_width}" stroke-opacity="0.85" stroke-linejoin="round" stroke-linecap="round"/>'
        )

# Add contour labels at strategic positions
label_positions = [
    (-20, 45, -4),
    (-15, 58, 0),
    (5, 62, 4),
    (20, 55, 8),
    (30, 50, 12),
    (35, 42, 16),
    (25, 33, 20),
    (10, 32, 24),
]

for lon_l, lat_l, temp_l in label_positions:
    if lon_min <= lon_l <= lon_max and lat_min <= lat_l <= lat_max:
        px = plot_x + (lon_l - lon_min) / (lon_max - lon_min) * plot_width
        py = plot_y + plot_height - (lat_l - lat_min) / (lat_max - lat_min) * plot_height
        svg_parts.append(
            f'<rect x="{px - 40}" y="{py - 26}" width="80" height="42" fill="white" fill-opacity="0.92" rx="5" '
            f'stroke="#666666" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{px}" y="{py + 8}" text-anchor="middle" fill="#333333" '
            f'style="font-size:34px;font-weight:bold;font-family:sans-serif">{temp_l}°C</text>'
        )

# Add colorbar with larger, more prominent labels
cb_width = 60
cb_height = plot_height * 0.75
cb_x = plot_x + plot_width + 70
cb_y = plot_y + (plot_height - cb_height) / 2

n_cb_segments = len(temp_colors)
seg_h = cb_height / n_cb_segments
for i, color in enumerate(temp_colors[::-1]):
    seg_y = cb_y + i * seg_h
    svg_parts.append(f'<rect x="{cb_x}" y="{seg_y:.1f}" width="{cb_width}" height="{seg_h + 1:.1f}" fill="{color}"/>')

svg_parts.append(
    f'<rect x="{cb_x}" y="{cb_y}" width="{cb_width}" height="{cb_height}" '
    f'fill="none" stroke="#333333" stroke-width="3"/>'
)

cb_labels = [24, 20, 16, 12, 8, 4, 0, -4]
for i, val in enumerate(cb_labels):
    label_y = cb_y + i * seg_h + seg_h / 2 + 14
    svg_parts.append(
        f'<text x="{cb_x + cb_width + 18}" y="{label_y:.1f}" fill="#333333" '
        f'style="font-size:42px;font-weight:bold;font-family:sans-serif">{val}°C</text>'
    )

svg_parts.append(
    f'<text x="{cb_x + cb_width / 2}" y="{cb_y - 30}" text-anchor="middle" fill="#333333" '
    f'style="font-size:44px;font-weight:bold;font-family:sans-serif">Temperature</text>'
)

custom_svg = "\n".join(svg_parts)

# Add dummy data point (required by pygal)
chart.add("", [(lon_min, lat_min)])

# Render base chart and inject custom SVG
base_svg = chart.render(is_unicode=True)
output_svg = base_svg.replace("</svg>", f"{custom_svg}\n</svg>")

# Convert to PNG using cairosvg
cairosvg.svg2png(bytestring=output_svg.encode("utf-8"), write_to="plot.png")
