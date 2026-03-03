""" pyplots.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: pygal 3.1.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-03
"""

import sys
from pathlib import Path


_script_dir = str(Path(__file__).parent)
sys.path = [p for p in sys.path if p != _script_dir]

import cairosvg  # noqa: E402
import numpy as np  # noqa: E402


# Data — Mandelbrot set computation
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
max_iter = 200
bailout = 256
grid_w, grid_h = 200, 143

real = np.linspace(x_min, x_max, grid_w)
imag = np.linspace(y_max, y_min, grid_h)
c = real[np.newaxis, :] + 1j * imag[:, np.newaxis]

z = np.zeros_like(c)
escape_iter = np.full(c.shape, max_iter, dtype=np.float64)
mask = np.ones(c.shape, dtype=bool)

for i in range(max_iter):
    z[mask] = z[mask] ** 2 + c[mask]
    escaped = mask & (np.abs(z) > bailout)
    log_zn = np.log(np.abs(z[escaped]))
    nu = np.log(log_zn / np.log(bailout)) / np.log(2)
    escape_iter[escaped] = i + 1 - nu
    mask[escaped] = False

inside = escape_iter >= max_iter
exterior = ~inside

# Viridis-inspired perceptually uniform colormap
viridis_stops = [
    (0.000, (68, 1, 84)),
    (0.125, (72, 36, 117)),
    (0.250, (62, 74, 137)),
    (0.375, (49, 104, 142)),
    (0.500, (38, 130, 142)),
    (0.625, (31, 158, 137)),
    (0.750, (53, 183, 121)),
    (0.875, (110, 206, 88)),
    (1.000, (253, 231, 37)),
]

lut_size = 1024
lut = np.zeros((lut_size, 3), dtype=int)
for idx in range(lut_size):
    t = idx / (lut_size - 1)
    for k in range(len(viridis_stops) - 1):
        t0, c0 = viridis_stops[k]
        t1, c1 = viridis_stops[k + 1]
        if t <= t1 + 1e-10:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0
            lut[idx] = [int(c0[ch] + (c1[ch] - c0[ch]) * f) for ch in range(3)]
            break

# Log-normalized color mapping
cell_colors = np.zeros((*c.shape, 3), dtype=int)
log_min, log_max = 0.0, 1.0
if np.any(exterior):
    iter_vals = escape_iter[exterior]
    log_vals = np.log(iter_vals + 1)
    log_min, log_max = log_vals.min(), log_vals.max()
    if log_max > log_min:
        normalized = (log_vals - log_min) / (log_max - log_min)
    else:
        normalized = np.zeros_like(log_vals)
    indices = np.clip((normalized * (lut_size - 1)).astype(int), 0, lut_size - 1)
    cell_colors[exterior] = lut[indices]

# SVG layout
W, H = 4800, 2700
margin_left = 320
margin_top = 200
margin_bottom = 200
plot_h = H - margin_top - margin_bottom
plot_w = int(plot_h * (x_max - x_min) / (y_max - y_min))
plot_x = margin_left
plot_y = margin_top
cell_w = plot_w / grid_w
cell_h = plot_h / grid_h

# Build SVG
svg = []
svg.append('<?xml version="1.0" encoding="utf-8"?>')
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
svg.append(f'<rect width="{W}" height="{H}" fill="white"/>')

# Title
svg.append(
    f'<text x="{W / 2}" y="80" text-anchor="middle" fill="#333" '
    f'style="font-size:56px;font-weight:600;font-family:sans-serif">'
    f"heatmap-mandelbrot \u00b7 pygal \u00b7 pyplots.ai</text>"
)

# Subtitle with mathematical formula
svg.append(
    f'<text x="{W / 2}" y="140" text-anchor="middle" fill="#666" '
    f'style="font-size:32px;font-weight:400;font-family:sans-serif">'
    f"z\u2099\u208a\u2081 = z\u2099\u00b2 + c \u00b7 "
    f"Escape time with smooth iteration count</text>"
)

# Mandelbrot heatmap cells
for i in range(grid_h):
    for j in range(grid_w):
        r, g, b = cell_colors[i, j]
        color = f"#{r:02x}{g:02x}{b:02x}"
        rx = plot_x + j * cell_w
        ry = plot_y + i * cell_h
        svg.append(
            f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{cell_w + 0.5:.1f}" height="{cell_h + 0.5:.1f}" fill="{color}"/>'
        )

# Plot border
svg.append(
    f'<rect x="{plot_x}" y="{plot_y}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#222" stroke-width="2"/>'
)

# X-axis ticks (Real axis)
x_tick_vals = [-2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0]
for val in x_tick_vals:
    frac = (val - x_min) / (x_max - x_min)
    tx = plot_x + frac * plot_w
    ty = plot_y + plot_h
    svg.append(f'<line x1="{tx:.1f}" y1="{ty}" x2="{tx:.1f}" y2="{ty + 15}" stroke="#333" stroke-width="2"/>')
    svg.append(
        f'<text x="{tx:.1f}" y="{ty + 55}" text-anchor="middle" fill="#333" '
        f'style="font-size:34px;font-family:sans-serif">{val:.1f}</text>'
    )

# X-axis label
svg.append(
    f'<text x="{plot_x + plot_w / 2}" y="{plot_y + plot_h + 130}" '
    f'text-anchor="middle" fill="#333" '
    f'style="font-size:44px;font-weight:600;font-family:sans-serif">'
    f"Real Axis (Re)</text>"
)

# Y-axis ticks (Imaginary axis)
y_tick_vals = [-1.0, -0.5, 0.0, 0.5, 1.0]
for val in y_tick_vals:
    frac = (y_max - val) / (y_max - y_min)
    ty = plot_y + frac * plot_h
    tx = plot_x
    label = f"{val:+.1f}i" if val != 0 else "0.0i"
    svg.append(f'<line x1="{tx - 15}" y1="{ty:.1f}" x2="{tx}" y2="{ty:.1f}" stroke="#333" stroke-width="2"/>')
    svg.append(
        f'<text x="{tx - 25}" y="{ty + 12:.1f}" text-anchor="end" fill="#333" '
        f'style="font-size:34px;font-family:sans-serif">{label}</text>'
    )

# Y-axis label (rotated)
y_lx = plot_x - 220
y_ly = plot_y + plot_h / 2
svg.append(
    f'<text x="{y_lx}" y="{y_ly}" text-anchor="middle" fill="#333" '
    f'style="font-size:44px;font-weight:600;font-family:sans-serif" '
    f'transform="rotate(-90, {y_lx}, {y_ly})">Imaginary Axis (Im)</text>'
)

# Colorbar
cb_x = plot_x + plot_w + 80
cb_w = 50
cb_top = plot_y + 50
cb_h = plot_h - 100
n_seg = 80

for s in range(n_seg):
    t = 1.0 - s / (n_seg - 1)
    color_idx = int(t * (lut_size - 1))
    r, g, b = lut[min(color_idx, lut_size - 1)]
    color = f"#{r:02x}{g:02x}{b:02x}"
    sy = cb_top + s * cb_h / n_seg
    svg.append(f'<rect x="{cb_x}" y="{sy:.1f}" width="{cb_w}" height="{cb_h / n_seg + 1:.1f}" fill="{color}"/>')

svg.append(
    f'<rect x="{cb_x}" y="{cb_top}" width="{cb_w}" height="{cb_h}" fill="none" stroke="#333" stroke-width="1.5"/>'
)

# Colorbar tick labels (iteration counts mapped from log scale)
for frac in [0.0, 0.25, 0.5, 0.75, 1.0]:
    t_color = 1.0 - frac
    log_val = log_min + t_color * (log_max - log_min)
    iter_val = np.exp(log_val) - 1
    ty = cb_top + frac * cb_h
    svg.append(
        f'<text x="{cb_x + cb_w + 15}" y="{ty + 10:.1f}" fill="#333" '
        f'style="font-size:28px;font-family:sans-serif">{iter_val:.0f}</text>'
    )

# Colorbar title
svg.append(
    f'<text x="{cb_x + cb_w / 2}" y="{cb_top - 25}" text-anchor="middle" '
    f'fill="#333" style="font-size:34px;font-weight:600;font-family:sans-serif">'
    f"Iterations</text>"
)

# Legend entry for interior (in-set) points
legend_y = cb_top + cb_h + 50
svg.append(f'<rect x="{cb_x}" y="{legend_y}" width="30" height="30" fill="black" stroke="#555" stroke-width="1"/>')
svg.append(
    f'<text x="{cb_x + 45}" y="{legend_y + 24}" fill="#333" style="font-size:28px;font-family:sans-serif">In set</text>'
)

svg.append("</svg>")

# Save SVG and PNG
svg_content = "\n".join(svg)

with open("plot.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to="plot.png", output_width=4800, output_height=2700)

# Interactive HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-mandelbrot - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; background: #f5f5f5; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {svg_content}
    </figure>
</body>
</html>
"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
