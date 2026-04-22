""" pyplots.ai
ternary-density: Ternary Density Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import math

import cairosvg
import numpy as np


np.random.seed(42)

# Triangle height for equilateral triangle with base = 1
H = math.sqrt(3) / 2

# Generate compositional data (sand/silt/clay sediment analysis)
# Create 3 clusters representing different sediment types

# Cluster 1: Sandy sediments (high sand)
n1 = 300
sand1 = np.random.beta(5, 2, n1) * 60 + 35
silt1 = np.random.beta(2, 3, n1) * (100 - sand1) * 0.6
clay1 = 100 - sand1 - silt1

# Cluster 2: Silty sediments (high silt)
n2 = 250
silt2 = np.random.beta(5, 2, n2) * 50 + 40
sand2 = np.random.beta(2, 4, n2) * (100 - silt2) * 0.5
clay2 = 100 - sand2 - silt2

# Cluster 3: Clay-rich sediments (high clay)
n3 = 250
clay3 = np.random.beta(4, 2, n3) * 45 + 40
sand3 = np.random.beta(2, 5, n3) * (100 - clay3) * 0.4
silt3 = 100 - sand3 - clay3

# Combine all clusters
sand = np.concatenate([sand1, sand2, sand3])
silt = np.concatenate([silt1, silt2, silt3])
clay = np.concatenate([clay1, clay2, clay3])

# Ensure non-negative values and normalize to sum to 100
sand = np.clip(sand, 0, 100)
silt = np.clip(silt, 0, 100)
clay = np.clip(clay, 0, 100)
total = sand + silt + clay
sand = sand / total * 100
silt = silt / total * 100
clay = clay / total * 100


# Convert ternary to Cartesian coordinates
# Top vertex = Clay (100%), Bottom-left = Sand (100%), Bottom-right = Silt (100%)
def ternary_to_cartesian(sand_pct, silt_pct, clay_pct):
    total = sand_pct + silt_pct + clay_pct
    _sand_frac, silt_frac, clay_frac = sand_pct / total, silt_pct / total, clay_pct / total
    x = 0.5 * (2 * silt_frac + clay_frac)
    y = H * clay_frac
    return x, y


# Convert data points
x_data = np.array([ternary_to_cartesian(sa, si, cl)[0] for sa, si, cl in zip(sand, silt, clay, strict=True)])
y_data = np.array([ternary_to_cartesian(sa, si, cl)[1] for sa, si, cl in zip(sand, silt, clay, strict=True)])

# Create density grid
grid_resolution = 100
xi = np.linspace(0, 1, grid_resolution)
yi = np.linspace(0, H, grid_resolution)
Xi, Yi = np.meshgrid(xi, yi)

# Convert grid to ternary to check if inside triangle
Ci = Yi / H  # clay fraction
Bi = Xi - Ci / 2  # silt fraction
Ai = 1 - Bi - Ci  # sand fraction

# Mask points outside the triangle
mask = (Ai >= -0.001) & (Bi >= -0.001) & (Ci >= -0.001) & (Ai <= 1.001) & (Bi <= 1.001) & (Ci <= 1.001)


# Simple 2D Gaussian KDE using numpy only
def gaussian_kde_numpy(x_data, y_data, xi, yi, bandwidth=None):
    n = len(x_data)
    if bandwidth is None:
        # Silverman's rule of thumb
        std_x = np.std(x_data)
        std_y = np.std(y_data)
        bandwidth = ((4 / (3 * n)) ** 0.2) * np.sqrt((std_x**2 + std_y**2) / 2)

    Z = np.zeros((len(yi), len(xi)))
    for i, yval in enumerate(yi):
        for j, xval in enumerate(xi):
            # Compute Gaussian kernel for each data point
            dx = (xval - x_data) / bandwidth
            dy = (yval - y_data) / bandwidth
            kernel_vals = np.exp(-0.5 * (dx**2 + dy**2))
            Z[i, j] = np.sum(kernel_vals) / (n * 2 * np.pi * bandwidth**2)
    return Z


# Compute KDE
Z = gaussian_kde_numpy(x_data, y_data, xi, yi)
Z = np.where(mask, Z, 0)

# Normalize Z for visualization
Z_norm = (Z - Z.min()) / (Z.max() - Z.min() + 1e-10)

# Viridis colormap values (sampled at key points)
viridis_colors = [
    (0.267004, 0.004874, 0.329415),  # 0.0
    (0.282327, 0.140926, 0.457517),  # 0.1
    (0.253935, 0.265254, 0.529983),  # 0.2
    (0.206756, 0.371758, 0.553117),  # 0.3
    (0.163625, 0.471133, 0.558148),  # 0.4
    (0.127568, 0.566949, 0.550556),  # 0.5
    (0.134692, 0.658636, 0.517649),  # 0.6
    (0.266941, 0.748751, 0.440573),  # 0.7
    (0.477504, 0.821444, 0.318195),  # 0.8
    (0.741388, 0.873449, 0.149561),  # 0.9
    (0.993248, 0.906157, 0.143936),  # 1.0
]


def get_viridis_color(value):
    """Get viridis color for a normalized value [0, 1]."""
    idx = min(int(value * 10), 9)
    frac = value * 10 - idx
    r = viridis_colors[idx][0] * (1 - frac) + viridis_colors[idx + 1][0] * frac
    g = viridis_colors[idx][1] * (1 - frac) + viridis_colors[idx + 1][1] * frac
    b = viridis_colors[idx][2] * (1 - frac) + viridis_colors[idx + 1][2] * frac
    return f"rgb({int(r * 255)},{int(g * 255)},{int(b * 255)})"


# Chart dimensions and coordinate mapping
chart_width = 3600
chart_height = 3600
margin = 200
plot_size = chart_width - 2 * margin

# Coordinate transformation functions (data space to pixel space)
x_min, x_max = -0.12, 1.12
y_min, y_max = -0.15, H + 0.15
x_range = x_max - x_min
y_range = y_max - y_min


def to_px(x, y):
    """Convert data coordinates to pixel coordinates."""
    px = margin + (x - x_min) / x_range * plot_size
    py = margin + (y_max - y) / y_range * plot_size
    return px, py


# Generate density heatmap as SVG rectangles
cell_size_x = xi[1] - xi[0]
cell_size_y = yi[1] - yi[0]
density_svg = '<g id="density-layer" opacity="0.85">\n'

# Draw density cells
for i in range(grid_resolution - 1):
    for j in range(grid_resolution - 1):
        if mask[i, j] and Z_norm[i, j] > 0.05:  # Only draw cells with significant density
            x_center = xi[j] + cell_size_x / 2
            y_center = yi[i] + cell_size_y / 2
            color = get_viridis_color(Z_norm[i, j])
            px, py = to_px(x_center, y_center)
            pw = cell_size_x / x_range * plot_size * 1.1
            ph = cell_size_y / y_range * plot_size * 1.1
            density_svg += f'  <rect x="{px - pw / 2:.1f}" y="{py - ph / 2:.1f}" width="{pw:.1f}" height="{ph:.1f}" fill="{color}" />\n'

density_svg += "</g>\n"

# Generate contour lines at specific density levels
contour_levels = [0.2, 0.4, 0.6, 0.8]
contour_svg = '<g id="contour-lines">\n'

for level in contour_levels:
    # Find contour at this level using simple thresholding
    threshold = level
    contour_mask = Z_norm >= threshold

    # Find boundary pixels
    boundary_points = []
    for i in range(1, grid_resolution - 1):
        for j in range(1, grid_resolution - 1):
            if contour_mask[i, j] and mask[i, j]:
                # Check if any neighbor is below threshold
                neighbors = [
                    contour_mask[i - 1, j],
                    contour_mask[i + 1, j],
                    contour_mask[i, j - 1],
                    contour_mask[i, j + 1],
                ]
                if not all(neighbors):
                    x_pt = xi[j]
                    y_pt = yi[i]
                    px, py = to_px(x_pt, y_pt)
                    boundary_points.append((px, py))

    # Draw boundary points as small circles for contour effect
    for px, py in boundary_points:
        contour_svg += f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="none" stroke="white" stroke-width="1.5" opacity="0.6" />\n'

contour_svg += "</g>\n"

# Triangle vertices in pixel coordinates
v_sand = to_px(0, 0)  # Bottom-left: 100% Sand
v_silt = to_px(1, 0)  # Bottom-right: 100% Silt
v_clay = to_px(0.5, H)  # Top: 100% Clay

# Triangle outline SVG
triangle_svg = f'''<g id="triangle-outline">
  <polygon points="{v_sand[0]:.1f},{v_sand[1]:.1f} {v_silt[0]:.1f},{v_silt[1]:.1f} {v_clay[0]:.1f},{v_clay[1]:.1f}" fill="none" stroke="#333333" stroke-width="4" />
</g>
'''

# Grid lines at 20%, 40%, 60%, 80%
grid_svg = '<g id="grid-lines" stroke="#888888" stroke-width="1.5" stroke-dasharray="10,6" opacity="0.5">\n'

for pct in [0.2, 0.4, 0.6, 0.8]:
    # Lines parallel to bottom (constant clay %)
    x1, y1 = ternary_to_cartesian(100 * (1 - pct), 0, 100 * pct)
    x2, y2 = ternary_to_cartesian(0, 100 * (1 - pct), 100 * pct)
    p1 = to_px(x1, y1)
    p2 = to_px(x2, y2)
    grid_svg += f'  <line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" />\n'

    # Lines parallel to left edge (constant silt %)
    x1, y1 = ternary_to_cartesian(100 * (1 - pct), 100 * pct, 0)
    x2, y2 = ternary_to_cartesian(0, 100 * pct, 100 * (1 - pct))
    p1 = to_px(x1, y1)
    p2 = to_px(x2, y2)
    grid_svg += f'  <line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" />\n'

    # Lines parallel to right edge (constant sand %)
    x1, y1 = ternary_to_cartesian(100 * pct, 0, 100 * (1 - pct))
    x2, y2 = ternary_to_cartesian(100 * pct, 100 * (1 - pct), 0)
    p1 = to_px(x1, y1)
    p2 = to_px(x2, y2)
    grid_svg += f'  <line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" />\n'

grid_svg += "</g>\n"

# Vertex labels
label_svg = f'''<g id="vertex-labels" font-family="sans-serif" font-weight="bold" fill="#333333">
  <text x="{v_sand[0] - 30:.1f}" y="{v_sand[1] + 70:.1f}" font-size="56" text-anchor="middle">SAND</text>
  <text x="{v_silt[0] + 30:.1f}" y="{v_silt[1] + 70:.1f}" font-size="56" text-anchor="middle">SILT</text>
  <text x="{v_clay[0]:.1f}" y="{v_clay[1] - 40:.1f}" font-size="56" text-anchor="middle">CLAY</text>
</g>
'''

# Percentage labels along edges
pct_svg = '<g id="percentage-labels" font-family="sans-serif" font-size="36" fill="#555555">\n'

for pct in [20, 40, 60, 80]:
    frac = pct / 100

    # Bottom edge (Sand-Silt axis)
    x_pt, y_pt = ternary_to_cartesian(100 * (1 - frac), 100 * frac, 0)
    px, py = to_px(x_pt, y_pt)
    pct_svg += f'  <text x="{px:.1f}" y="{py + 45:.1f}" text-anchor="middle">{pct}</text>\n'

    # Left edge (Sand-Clay axis)
    x_pt, y_pt = ternary_to_cartesian(100 * (1 - frac), 0, 100 * frac)
    px, py = to_px(x_pt, y_pt)
    pct_svg += f'  <text x="{px - 35:.1f}" y="{py + 10:.1f}" text-anchor="end">{pct}</text>\n'

    # Right edge (Silt-Clay axis)
    x_pt, y_pt = ternary_to_cartesian(0, 100 * (1 - frac), 100 * frac)
    px, py = to_px(x_pt, y_pt)
    pct_svg += f'  <text x="{px + 35:.1f}" y="{py + 10:.1f}" text-anchor="start">{pct}</text>\n'

pct_svg += "</g>\n"

# Colorbar
cbar_x = chart_width - margin + 40
cbar_y = margin + 200
cbar_width = 40
cbar_height = plot_size - 400

colorbar_svg = '<g id="colorbar">\n'
colorbar_svg += f'  <text x="{cbar_x + cbar_width / 2:.1f}" y="{cbar_y - 30:.1f}" font-family="sans-serif" font-size="44" font-weight="bold" text-anchor="middle" fill="#333333">Density</text>\n'

# Gradient rectangles
n_cbar_steps = 50
for i in range(n_cbar_steps):
    val = 1 - i / n_cbar_steps
    color = get_viridis_color(val)
    cy = cbar_y + i / n_cbar_steps * cbar_height
    ch = cbar_height / n_cbar_steps + 1
    colorbar_svg += (
        f'  <rect x="{cbar_x:.1f}" y="{cy:.1f}" width="{cbar_width:.1f}" height="{ch:.1f}" fill="{color}" />\n'
    )

# Colorbar border
colorbar_svg += f'  <rect x="{cbar_x:.1f}" y="{cbar_y:.1f}" width="{cbar_width:.1f}" height="{cbar_height:.1f}" fill="none" stroke="#333333" stroke-width="2" />\n'

# Colorbar labels
colorbar_svg += f'  <text x="{cbar_x + cbar_width + 15:.1f}" y="{cbar_y + 15:.1f}" font-family="sans-serif" font-size="32" fill="#333333">High</text>\n'
colorbar_svg += f'  <text x="{cbar_x + cbar_width + 15:.1f}" y="{cbar_y + cbar_height + 5:.1f}" font-family="sans-serif" font-size="32" fill="#333333">Low</text>\n'
colorbar_svg += "</g>\n"

# Title
title_y = 100
title_svg = f'''<g id="title">
  <text x="{chart_width / 2:.1f}" y="{title_y:.1f}" font-family="sans-serif" font-size="72" font-weight="bold" text-anchor="middle" fill="#333333">Sediment Composition Distribution</text>
  <text x="{chart_width / 2:.1f}" y="{title_y + 60:.1f}" font-family="sans-serif" font-size="48" text-anchor="middle" fill="#555555">ternary-density · pygal · pyplots.ai</text>
</g>
'''

# Clip path to restrict density to triangle
clip_path_svg = f'''<defs>
  <clipPath id="triangle-clip">
    <polygon points="{v_sand[0]:.1f},{v_sand[1]:.1f} {v_silt[0]:.1f},{v_silt[1]:.1f} {v_clay[0]:.1f},{v_clay[1]:.1f}" />
  </clipPath>
</defs>
'''

# Assemble full SVG
svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{chart_width}" height="{chart_height}" viewBox="0 0 {chart_width} {chart_height}">
  <rect width="100%" height="100%" fill="white" />
  {clip_path_svg}
  {title_svg}
  <g clip-path="url(#triangle-clip)">
    {density_svg}
    {contour_svg}
  </g>
  {grid_svg}
  {triangle_svg}
  {label_svg}
  {pct_svg}
  {colorbar_svg}
</svg>
'''

# Save as HTML (SVG)
with open("plot.html", "w") as f:
    f.write(svg_content)

# Convert to PNG
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to="plot.png")
