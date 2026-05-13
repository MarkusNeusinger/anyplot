"""anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-13
"""

import math
import os

import cairosvg
import matplotlib.cm as cm
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data: monthly household energy consumption (kWh) across 5 years
np.random.seed(42)
years = [2019, 2020, 2021, 2022, 2023]
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
n_radial = len(years)
n_angular = len(months)

# Seasonal pattern: winter peaks in Jan/Dec, mild in spring/autumn
base = np.array([90, 85, 74, 63, 58, 65, 74, 71, 63, 67, 78, 92], dtype=float)
data = np.zeros((n_radial, n_angular))
for i in range(n_radial):
    data[i] = base * (1.0 + i * 0.018) + np.random.normal(0, 2.5, n_angular)

vmin, vmax = data.min(), data.max()


def val_to_hex(val):
    t = float(np.clip((val - vmin) / (vmax - vmin), 0, 1))
    r, g, b, _ = cm.viridis(t)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


# SVG canvas
W, H = 4800, 2700
CX, CY = 2000, 1380  # polar chart center
R_MIN, R_MAX = 320, 1100
ring_h = (R_MAX - R_MIN) / n_radial  # 156 px per ring


def to_xy(r, theta):
    """Polar → SVG coords; theta=0 at 12 o'clock, increases clockwise."""
    return CX + r * math.sin(theta), CY - r * math.cos(theta)


def arc_path(r_in, r_out, th0, th1):
    x1, y1 = to_xy(r_out, th0)
    x2, y2 = to_xy(r_out, th1)
    x3, y3 = to_xy(r_in, th1)
    x4, y4 = to_xy(r_in, th0)
    la = 1 if (th1 - th0) > math.pi else 0
    return (
        f"M{x1:.1f},{y1:.1f}"
        f" A{r_out:.0f},{r_out:.0f} 0 {la},1 {x2:.1f},{y2:.1f}"
        f" L{x3:.1f},{y3:.1f}"
        f" A{r_in:.0f},{r_in:.0f} 0 {la},0 {x4:.1f},{y4:.1f}Z"
    )


# Build SVG
lines = []
lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">')
lines.append(f'<rect width="{W}" height="{H}" fill="{PAGE_BG}"/>')

# Title and subtitle
lines.append(
    f'<text x="{W // 2}" y="112" text-anchor="middle" '
    f'fill="{INK}" font-size="54" font-weight="bold" font-family="sans-serif">'
    f"heatmap-polar · pygal · anyplot.ai</text>"
)
lines.append(
    f'<text x="{W // 2}" y="182" text-anchor="middle" '
    f'fill="{INK_SOFT}" font-size="36" font-family="sans-serif">'
    f"Monthly Household Energy Consumption by Year (kWh)</text>"
)

# Heatmap cells (angular × radial)
angle_step = 2 * math.pi / n_angular
gap = 0.022  # radians removed from each cell edge

for i in range(n_radial):
    r_in = R_MIN + i * ring_h + 4
    r_out = R_MIN + (i + 1) * ring_h - 4
    for j in range(n_angular):
        th_s = j * angle_step + gap
        th_e = (j + 1) * angle_step - gap
        lines.append(f'<path d="{arc_path(r_in, r_out, th_s, th_e)}" fill="{val_to_hex(data[i, j])}"/>')

# Concentric ring separators (background-colored circles)
for k in range(n_radial + 1):
    r = R_MIN + k * ring_h
    lines.append(f'<circle cx="{CX}" cy="{CY}" r="{r:.0f}" fill="none" stroke="{PAGE_BG}" stroke-width="6"/>')

# Month labels (angular axis, outside outermost ring)
for j, month in enumerate(months):
    theta = (j + 0.5) * angle_step
    lx, ly = to_xy(R_MAX + 88, theta)
    lines.append(
        f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" '
        f'dominant-baseline="middle" fill="{INK}" font-size="40" '
        f'font-family="sans-serif" font-weight="500">{month}</text>'
    )

# Year legend (right of chart, maps color swatch to ring)
leg_x = 3350
leg_y0 = CY - 250
lines.append(
    f'<text x="{leg_x}" y="{leg_y0}" fill="{INK}" font-size="30" '
    f'font-family="sans-serif" font-weight="600">Year (inner → outer)</text>'
)
for i, year in enumerate(years):
    sy = leg_y0 + 68 + i * 98
    avg_color = val_to_hex(float(data[i].mean()))
    lines.append(f'<rect x="{leg_x}" y="{sy - 25}" width="68" height="50" rx="5" fill="{avg_color}"/>')
    lines.append(
        f'<text x="{leg_x + 90}" y="{sy + 3}" fill="{INK_SOFT}" '
        f'dominant-baseline="middle" font-size="34" font-family="sans-serif">{year}</text>'
    )

# Colorbar (far right, vertical viridis gradient)
cb_x = 4260
cb_y_top = 350
cb_h = 2000
cb_w = 72
n_steps = 256
step = cb_h / n_steps
for k in range(n_steps):
    t = k / (n_steps - 1)
    y_pos = cb_y_top + cb_h - (k + 1) * step
    lines.append(
        f'<rect x="{cb_x}" y="{y_pos:.1f}" width="{cb_w}" '
        f'height="{step + 0.5:.1f}" fill="{val_to_hex(vmin + t * (vmax - vmin))}"/>'
    )

# Colorbar border
lines.append(
    f'<rect x="{cb_x}" y="{cb_y_top}" width="{cb_w}" height="{cb_h}" '
    f'fill="none" stroke="{INK_SOFT}" stroke-width="1.5" opacity="0.3"/>'
)

# Colorbar tick labels (min, mid, max)
for t_val, db in [(0.0, "auto"), (0.5, "middle"), (1.0, "hanging")]:
    val = vmin + t_val * (vmax - vmin)
    y_tick = cb_y_top + cb_h * (1.0 - t_val)
    lines.append(
        f'<text x="{cb_x + cb_w + 18}" y="{y_tick:.0f}" '
        f'fill="{INK_SOFT}" font-size="28" font-family="sans-serif" '
        f'dominant-baseline="{db}">{val:.0f}</text>'
    )

# Colorbar unit label
lines.append(
    f'<text x="{cb_x + cb_w // 2}" y="{cb_y_top - 24}" '
    f'text-anchor="middle" fill="{INK_MUTED}" font-size="28" font-family="sans-serif">'
    f"kWh</text>"
)

lines.append("</svg>")
svg_str = "\n".join(lines)

# Save HTML (pygal output format: interactive SVG in browser)
html_str = (
    f'<!DOCTYPE html><html><head><meta charset="utf-8">'
    f"<style>body{{margin:0;background:{PAGE_BG};}}</style></head>"
    f"<body>{svg_str}</body></html>"
)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_str)

# Save PNG via cairosvg (same conversion pipeline pygal uses internally)
cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=W, output_height=H)
