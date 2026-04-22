""" pyplots.ai
contour-density: Density Contour Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-01
"""

import sys
from pathlib import Path


# Remove script directory from path to avoid name collision with pygal package
_script_dir = str(Path(__file__).parent)
sys.path = [p for p in sys.path if p != _script_dir]

import cairosvg  # noqa: E402
import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402
from scipy import stats  # noqa: E402


# Data: Bivariate distribution with multiple clusters (temperature vs humidity sensors)
np.random.seed(42)

# Create realistic clustered data - weather sensor readings
n_samples = 500

# Cluster 1: Morning readings (cool, humid)
n1 = 180
x1 = np.random.normal(15, 2.5, n1)  # Temperature (°C)
y1 = np.random.normal(75, 8, n1)  # Humidity (%)

# Cluster 2: Midday readings (warm, moderate humidity)
n2 = 200
x2 = np.random.normal(28, 3, n2)
y2 = np.random.normal(45, 10, n2)

# Cluster 3: Evening readings (moderate temp, varied humidity)
n3 = 120
x3 = np.random.normal(22, 4, n3)
y3 = np.random.normal(60, 12, n3)

# Combine all data
x_data = np.concatenate([x1, x2, x3])
y_data = np.concatenate([y1, y2, y3])

# Compute 2D KDE (Kernel Density Estimation)
n_grid = 100
x_min, x_max = x_data.min() - 2, x_data.max() + 2
y_min, y_max = y_data.min() - 5, y_data.max() + 5

x_grid = np.linspace(x_min, x_max, n_grid)
y_grid = np.linspace(y_min, y_max, n_grid)
X, Y = np.meshgrid(x_grid, y_grid)
positions = np.vstack([X.ravel(), Y.ravel()])

# Fit KDE
values = np.vstack([x_data, y_data])
kernel = stats.gaussian_kde(values)
Z = np.reshape(kernel(positions).T, X.shape)

z_min, z_max = Z.min(), Z.max()

# Sequential colormap for density (light to dark blue with Python colors)
colormap = [
    "#f7fbff",
    "#deebf7",
    "#c6dbef",
    "#9ecae1",
    "#6baed6",
    "#4292c6",
    "#306998",  # Python Blue
    "#214e6b",
    "#08306b",
]


def interpolate_color(value, vmin, vmax):
    """Get color for value using linear interpolation."""
    if vmax == vmin:
        return colormap[len(colormap) // 2]
    norm = max(0, min(1, (value - vmin) / (vmax - vmin)))
    pos = norm * (len(colormap) - 1)
    i1, i2 = int(pos), min(int(pos) + 1, len(colormap) - 1)
    frac = pos - i1
    c1, c2 = colormap[i1], colormap[i2]
    r = int(int(c1[1:3], 16) + (int(c2[1:3], 16) - int(c1[1:3], 16)) * frac)
    g = int(int(c1[3:5], 16) + (int(c2[3:5], 16) - int(c1[3:5], 16)) * frac)
    b = int(int(c1[5:7], 16) + (int(c2[5:7], 16) - int(c1[5:7], 16)) * frac)
    return f"#{r:02x}{g:02x}{b:02x}"


# Style for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=72,
    legend_font_size=48,
    label_font_size=42,
    value_font_size=36,
    font_family="sans-serif",
)

# Create base XY chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="contour-density · pygal · pyplots.ai",
    show_legend=False,
    margin=120,
    margin_top=200,
    margin_bottom=200,
    margin_left=300,
    margin_right=350,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    x_title="",
    y_title="",
)

# Plot dimensions (matching chart margins)
plot_x = 300
plot_y = 200
plot_width = 4800 - 300 - 350
plot_height = 2700 - 200 - 200

# Cell size
cell_w = plot_width / (n_grid - 1)
cell_h = plot_height / (n_grid - 1)

# Build SVG content
svg_parts = []

# Draw filled density cells
for i in range(n_grid - 1):
    for j in range(n_grid - 1):
        # Average of 4 corners for cell color
        cell_val = (Z[i, j] + Z[i, j + 1] + Z[i + 1, j] + Z[i + 1, j + 1]) / 4
        color = interpolate_color(cell_val, z_min, z_max)
        cx = plot_x + j * cell_w
        cy = plot_y + plot_height - (i + 1) * cell_h
        svg_parts.append(
            f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell_w + 0.5:.1f}" '
            f'height="{cell_h + 0.5:.1f}" fill="{color}" stroke="none"/>'
        )

# Draw contour lines using marching squares
n_contour_levels = 10
contour_levels = np.linspace(z_min + (z_max - z_min) * 0.1, z_max * 0.95, n_contour_levels)

for level in contour_levels:
    for i in range(n_grid - 1):
        for j in range(n_grid - 1):
            z00, z01 = Z[i, j], Z[i, j + 1]
            z10, z11 = Z[i + 1, j], Z[i + 1, j + 1]

            # Marching squares case
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

            # Cell position
            x0 = plot_x + j * cell_w
            y0 = plot_y + plot_height - (i + 1) * cell_h

            # Linear interpolation helper
            def lerp(v1, v2, lv):
                if abs(v2 - v1) < 1e-10:
                    return 0.5
                return (lv - v1) / (v2 - v1)

            # Edge midpoints
            left = (x0, y0 + cell_h * lerp(z00, z10, level))
            right = (x0 + cell_w, y0 + cell_h * lerp(z01, z11, level))
            top = (x0 + cell_w * lerp(z10, z11, level), y0 + cell_h)
            bottom = (x0 + cell_w * lerp(z00, z01, level), y0)

            segments = []
            if case in [1, 14]:
                segments.append((left, bottom))
            elif case in [2, 13]:
                segments.append((bottom, right))
            elif case in [3, 12]:
                segments.append((left, right))
            elif case in [4, 11]:
                segments.append((right, top))
            elif case == 5:
                segments.append((left, top))
                segments.append((bottom, right))
            elif case in [6, 9]:
                segments.append((bottom, top))
            elif case in [7, 8]:
                segments.append((left, top))
            elif case == 10:
                segments.append((left, bottom))
                segments.append((right, top))

            for (x1, y1), (x2, y2) in segments:
                svg_parts.append(
                    f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                    f'stroke="#333333" stroke-width="2" stroke-opacity="0.5"/>'
                )

# Optional: Add scatter points overlay (semi-transparent) for context
for px, py in zip(x_data[::5], y_data[::5], strict=True):  # Sample every 5th point
    sx = plot_x + (px - x_min) / (x_max - x_min) * plot_width
    sy = plot_y + plot_height - (py - y_min) / (y_max - y_min) * plot_height
    svg_parts.append(
        f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="4" fill="#FFD43B" stroke="#333" stroke-width="0.5" opacity="0.6"/>'
    )

# Axis frame
svg_parts.append(
    f'<rect x="{plot_x}" y="{plot_y}" width="{plot_width}" height="{plot_height}" '
    f'fill="none" stroke="#333333" stroke-width="2"/>'
)

# X-axis labels and ticks
n_x_ticks = 7
for i in range(n_x_ticks):
    frac = i / (n_x_ticks - 1)
    tick_x = plot_x + frac * plot_width
    tick_y = plot_y + plot_height
    val = x_min + frac * (x_max - x_min)
    svg_parts.append(
        f'<line x1="{tick_x:.1f}" y1="{tick_y}" x2="{tick_x:.1f}" y2="{tick_y + 15}" stroke="#333333" stroke-width="2"/>'
    )
    svg_parts.append(
        f'<text x="{tick_x:.1f}" y="{tick_y + 55}" text-anchor="middle" fill="#333333" '
        f'style="font-size:36px;font-family:sans-serif">{val:.0f}</text>'
    )

# X-axis title
svg_parts.append(
    f'<text x="{plot_x + plot_width / 2}" y="{plot_y + plot_height + 130}" text-anchor="middle" '
    f'fill="#333333" style="font-size:44px;font-weight:bold;font-family:sans-serif">Temperature (°C)</text>'
)

# Y-axis labels and ticks
n_y_ticks = 7
for i in range(n_y_ticks):
    frac = i / (n_y_ticks - 1)
    tick_y = plot_y + plot_height - frac * plot_height
    tick_x = plot_x
    val = y_min + frac * (y_max - y_min)
    svg_parts.append(
        f'<line x1="{tick_x - 15}" y1="{tick_y:.1f}" x2="{tick_x}" y2="{tick_y:.1f}" stroke="#333333" stroke-width="2"/>'
    )
    svg_parts.append(
        f'<text x="{tick_x - 25}" y="{tick_y + 12:.1f}" text-anchor="end" fill="#333333" '
        f'style="font-size:36px;font-family:sans-serif">{val:.0f}</text>'
    )

# Y-axis title (rotated)
y_title_x = plot_x - 180
y_title_y = plot_y + plot_height / 2
svg_parts.append(
    f'<text x="{y_title_x}" y="{y_title_y}" text-anchor="middle" fill="#333333" '
    f'style="font-size:44px;font-weight:bold;font-family:sans-serif" '
    f'transform="rotate(-90, {y_title_x}, {y_title_y})">Humidity (%)</text>'
)

# Colorbar
cb_width = 50
cb_height = plot_height * 0.85
cb_x = plot_x + plot_width + 60
cb_y = plot_y + (plot_height - cb_height) / 2

# Colorbar gradient
n_cb_segments = 80
seg_h = cb_height / n_cb_segments
for i in range(n_cb_segments):
    seg_val = z_max - (z_max - z_min) * i / (n_cb_segments - 1)
    seg_color = interpolate_color(seg_val, z_min, z_max)
    seg_y = cb_y + i * seg_h
    svg_parts.append(
        f'<rect x="{cb_x}" y="{seg_y:.1f}" width="{cb_width}" height="{seg_h + 1:.1f}" fill="{seg_color}"/>'
    )

# Colorbar border
svg_parts.append(
    f'<rect x="{cb_x}" y="{cb_y}" width="{cb_width}" height="{cb_height}" fill="none" stroke="#333333" stroke-width="2"/>'
)

# Colorbar labels (density values)
n_cb_labels = 5
for i in range(n_cb_labels):
    frac = i / (n_cb_labels - 1)
    val = z_max - (z_max - z_min) * frac
    label_y = cb_y + frac * cb_height + 12
    # Format as scientific notation for small density values
    svg_parts.append(
        f'<text x="{cb_x + cb_width + 15}" y="{label_y:.1f}" fill="#333333" '
        f'style="font-size:32px;font-family:sans-serif">{val:.4f}</text>'
    )

# Colorbar title
cb_title_x = cb_x + cb_width / 2
cb_title_y = cb_y - 30
svg_parts.append(
    f'<text x="{cb_title_x}" y="{cb_title_y}" text-anchor="middle" fill="#333333" '
    f'style="font-size:38px;font-weight:bold;font-family:sans-serif">Density</text>'
)

# Combine all SVG parts
custom_svg = "\n".join(svg_parts)

# Add dummy data point (required by pygal)
chart.add("", [(0, 0)])

# Render base chart and inject custom SVG
base_svg = chart.render(is_unicode=True)

# Insert custom contour SVG before the closing </svg> tag
output_svg = base_svg.replace("</svg>", f"{custom_svg}\n</svg>")

# Save SVG
with open("plot.svg", "w", encoding="utf-8") as f:
    f.write(output_svg)

# Convert to PNG using cairosvg
cairosvg.svg2png(bytestring=output_svg.encode("utf-8"), write_to="plot.png")

# Save interactive HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>contour-density - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f5f5f5; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {output_svg}
    </figure>
</body>
</html>
"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
