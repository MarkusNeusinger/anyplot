""" anyplot.ai
contour-basic: Basic Contour Plot
Library: pygal 3.1.0 | Python 3.14.4
Quality: 89/100 | Created: 2026-04-24
"""

import os
import re
import sys


# Script filename shadows the installed `pygal` package when run as `python pygal.py`;
# dropping the script directory from sys.path lets the real package resolve.
sys.path.pop(0)

import cairosvg  # noqa: E402
import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
LINE_COLOR = "#FAF8F1" if THEME == "light" else "#F0EFE8"
LINE_OPACITY = 0.65 if THEME == "light" else 0.80

# Viridis colormap stops (sequential, perceptually uniform, CVD-safe)
VIRIDIS_STOPS = [
    (0.00, "#440154"),
    (0.10, "#482475"),
    (0.20, "#414487"),
    (0.30, "#355f8d"),
    (0.40, "#2a788e"),
    (0.50, "#21918c"),
    (0.60, "#22a884"),
    (0.70, "#44bf70"),
    (0.80, "#7ad151"),
    (0.90, "#bddf26"),
    (1.00, "#fde725"),
]
VIR_T = np.array([s[0] for s in VIRIDIS_STOPS])
VIR_R = np.array([int(s[1][1:3], 16) for s in VIRIDIS_STOPS])
VIR_G = np.array([int(s[1][3:5], 16) for s in VIRIDIS_STOPS])
VIR_B = np.array([int(s[1][5:7], 16) for s in VIRIDIS_STOPS])

# Data — simulated topographic elevation map of a 10 km x 10 km mountain region
np.random.seed(42)
n_points = 80
x = np.linspace(0, 10, n_points)
y = np.linspace(0, 10, n_points)
X, Y = np.meshgrid(x, y)

elevation = (
    850 * np.exp(-((X - 7) ** 2 + (Y - 7) ** 2) / 4.0)
    + 550 * np.exp(-((X - 2.5) ** 2 + (Y - 3) ** 2) / 3.0)
    - 180 * np.exp(-((X - 5) ** 2 + (Y - 5) ** 2) / 8.0)
    + 12 * X
    + 350
)

z_min, z_max = float(elevation.min()), float(elevation.max())
primary_peak = (7.0, 7.0)
secondary_peak = (2.5, 3.0)
primary_elev = int(
    round(
        float(
            850 * np.exp(0)
            + 550 * np.exp(-((7 - 2.5) ** 2 + (7 - 3) ** 2) / 3.0)
            - 180 * np.exp(-((7 - 5) ** 2 + (7 - 5) ** 2) / 8.0)
            + 12 * 7
            + 350
        )
    )
)
secondary_elev = int(
    round(
        float(
            850 * np.exp(-((2.5 - 7) ** 2 + (3 - 7) ** 2) / 4.0)
            + 550 * np.exp(0)
            - 180 * np.exp(-((2.5 - 5) ** 2 + (3 - 5) ** 2) / 8.0)
            + 12 * 2.5
            + 350
        )
    )
)

# Canvas and plot layout (pygal margins define the reserved area around the plot)
CANVAS_W, CANVAS_H = 4800, 2700
MARGIN_L, MARGIN_R = 360, 620
MARGIN_T, MARGIN_B = 220, 260

font = "DejaVu Sans, Helvetica, Arial, sans-serif"

# Style carries theme tokens + peak marker colors (Okabe-Ito orange & blue —
# deliberately off-palette from viridis so markers stay legible on any elevation tone).
custom_style = Style(
    background=PAGE_BG,
    plot_background="transparent",
    foreground=INK_SOFT,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=("#D55E00", "#0072B2"),
    font_family=font,
    title_font_family=font,
    label_font_family=font,
    major_label_font_family=font,
    tooltip_font_family=font,
    tooltip_font_size=34,
    legend_font_size=38,
    stroke_width=6,
    opacity=".95",
    opacity_hover=".65",
    transition="200ms ease-in",
)

# Pygal XY chart: peak markers are real data, rendered natively with hover tooltips.
# Interactivity (pygal's default JS) is kept enabled — the HTML export is a live chart.
chart = pygal.XY(
    width=CANVAS_W,
    height=CANVAS_H,
    style=custom_style,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    margin_left=MARGIN_L,
    margin_right=MARGIN_R,
    margin_top=MARGIN_T,
    margin_bottom=MARGIN_B,
    xrange=(0, 10),
    range=(0, 10),
    dots_size=22,
    stroke=False,
    truncate_label=-1,
)

chart.add("Primary Peak", [{"value": primary_peak, "label": f"Primary Peak · {primary_elev} m"}])
chart.add("Secondary Peak", [{"value": secondary_peak, "label": f"Secondary Peak · {secondary_elev} m"}])

# Render pygal first so we can read back its exact plot-box placement.
# Pygal applies a small internal axis-range padding inside the margin box; we
# back-compute it from the two peak dots' pixel positions so the contour aligns
# perfectly with the interactive markers pygal drew.
base_svg = chart.render(is_unicode=True)

dot_re = re.compile(r'<circle cx="([-\d.]+)" cy="([-\d.]+)"[^>]*class="dot')
peaks = [(float(cx), float(cy)) for cx, cy in dot_re.findall(base_svg)]
(p1x, p1y), (p2x, p2y) = peaks[0], peaks[1]
x_scale = (p1x - p2x) / (primary_peak[0] - secondary_peak[0])
x_off = p1x - primary_peak[0] * x_scale
y_scale = (p1y - p2y) / (primary_peak[1] - secondary_peak[1])
y_off = p1y - primary_peak[1] * y_scale

# Absolute plot box in SVG coords (inside pygal's translated plot group → + margins)
plot_x = MARGIN_L + x_off
plot_y = MARGIN_T + y_off + 10 * y_scale
plot_width = 10 * x_scale
plot_height = -10 * y_scale

cell_w = plot_width / (n_points - 1)
cell_h = plot_height / (n_points - 1)

svg_parts = []

# Filled contour — color each grid cell by its mean elevation.
# Vectorized viridis lookup: piecewise-linear interpolation across the 11 stops.
cell_mean = (elevation[:-1, :-1] + elevation[:-1, 1:] + elevation[1:, :-1] + elevation[1:, 1:]) / 4
cell_t = np.clip((cell_mean - z_min) / (z_max - z_min), 0.0, 1.0)
cell_idx = np.clip(np.searchsorted(VIR_T, cell_t, side="right") - 1, 0, len(VIRIDIS_STOPS) - 2)
cell_span = VIR_T[cell_idx + 1] - VIR_T[cell_idx]
cell_f = np.where(cell_span == 0, 0.0, (cell_t - VIR_T[cell_idx]) / np.where(cell_span == 0, 1, cell_span))
cell_r = (VIR_R[cell_idx] + (VIR_R[cell_idx + 1] - VIR_R[cell_idx]) * cell_f).astype(int)
cell_g = (VIR_G[cell_idx] + (VIR_G[cell_idx + 1] - VIR_G[cell_idx]) * cell_f).astype(int)
cell_b = (VIR_B[cell_idx] + (VIR_B[cell_idx + 1] - VIR_B[cell_idx]) * cell_f).astype(int)

for i in range(n_points - 1):
    for j in range(n_points - 1):
        cx = plot_x + j * cell_w
        cy = plot_y + plot_height - (i + 1) * cell_h
        color = f"#{cell_r[i, j]:02x}{cell_g[i, j]:02x}{cell_b[i, j]:02x}"
        svg_parts.append(
            f'<rect x="{cx:.2f}" y="{cy:.2f}" width="{cell_w + 0.6:.2f}" '
            f'height="{cell_h + 0.6:.2f}" fill="{color}" stroke="none"/>'
        )

# Marching-squares contour extraction — inlined per level.
# Minor lines every 50 m (subtle); major lines every 200 m (emphasized, labeled).
minor_levels = list(range(400, 1251, 50))
major_levels = list(range(400, 1251, 200))
major_set = set(major_levels)
all_levels = sorted(set(minor_levels + major_levels))

major_segments_by_level = {}

for lvl in all_levels:
    is_major = lvl in major_set
    segments = []
    for i in range(n_points - 1):
        for j in range(n_points - 1):
            z00 = elevation[i, j]
            z01 = elevation[i, j + 1]
            z10 = elevation[i + 1, j]
            z11 = elevation[i + 1, j + 1]

            case = 0
            if z00 >= lvl:
                case |= 1
            if z01 >= lvl:
                case |= 2
            if z11 >= lvl:
                case |= 4
            if z10 >= lvl:
                case |= 8
            if case == 0 or case == 15:
                continue

            x0 = plot_x + j * cell_w
            y_bot = plot_y + plot_height - i * cell_h
            y_top = plot_y + plot_height - (i + 1) * cell_h

            # Inline lerp: fraction along each cell edge where the iso-level crosses.
            fl = 0.5 if abs(z10 - z00) < 1e-10 else (lvl - z00) / (z10 - z00)
            fr = 0.5 if abs(z11 - z01) < 1e-10 else (lvl - z01) / (z11 - z01)
            ft = 0.5 if abs(z11 - z10) < 1e-10 else (lvl - z10) / (z11 - z10)
            fb = 0.5 if abs(z01 - z00) < 1e-10 else (lvl - z00) / (z01 - z00)

            left = (x0, y_bot - cell_h * fl)
            right = (x0 + cell_w, y_bot - cell_h * fr)
            top = (x0 + cell_w * ft, y_top)
            bottom = (x0 + cell_w * fb, y_bot)

            if case == 1 or case == 14:
                segments.append((left, bottom))
            elif case == 2 or case == 13:
                segments.append((bottom, right))
            elif case == 3 or case == 12:
                segments.append((left, right))
            elif case == 4 or case == 11:
                segments.append((right, top))
            elif case == 5:
                segments.append((left, top))
                segments.append((bottom, right))
            elif case == 6 or case == 9:
                segments.append((bottom, top))
            elif case == 7 or case == 8:
                segments.append((left, top))
            elif case == 10:
                segments.append((left, bottom))
                segments.append((right, top))

    stroke_w = 4 if is_major else 2
    stroke_op = LINE_OPACITY if is_major else 0.30
    for (x1, y1), (x2, y2) in segments:
        svg_parts.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{LINE_COLOR}" stroke-width="{stroke_w}" stroke-opacity="{stroke_op}"/>'
        )

    if is_major:
        major_segments_by_level[lvl] = segments

# Contour level labels — one label per major contour. Each label is placed at the
# segment midpoint that maximizes the distance to every already-placed anchor (peak
# markers + prior labels), so labels fan out around the primary peak instead of
# overlapping markers or piling up. A PAGE_BG halo keeps digits legible against fill.
label_font_px = 40
placed_positions = [(p1x, p1y), (p2x, p2y)]
for lvl, segs in major_segments_by_level.items():
    if not segs:
        continue
    best_cx, best_cy, best_score = 0.0, 0.0, -1.0
    for (x1, y1), (x2, y2) in segs:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        nearest_sq = min((mx - px) ** 2 + (my - py) ** 2 for px, py in placed_positions)
        if nearest_sq > best_score:
            best_score = nearest_sq
            best_cx, best_cy = mx, my
    cx, cy = best_cx, best_cy
    placed_positions.append((cx, cy))
    text = f"{lvl} m"
    svg_parts.append(
        f'<text x="{cx:.2f}" y="{cy + 14:.2f}" text-anchor="middle" '
        f'fill="none" stroke="{PAGE_BG}" stroke-width="9" stroke-linejoin="round" '
        f'style="font-size:{label_font_px}px;font-family:{font};font-weight:600">{text}</text>'
    )
    svg_parts.append(
        f'<text x="{cx:.2f}" y="{cy + 14:.2f}" text-anchor="middle" '
        f'fill="{INK}" style="font-size:{label_font_px}px;font-family:{font};font-weight:600">{text}</text>'
    )

# L-shaped frame (left + bottom only)
svg_parts.append(
    f'<line x1="{plot_x:.2f}" y1="{plot_y:.2f}" x2="{plot_x:.2f}" y2="{plot_y + plot_height:.2f}" '
    f'stroke="{INK_SOFT}" stroke-width="2.5"/>'
)
svg_parts.append(
    f'<line x1="{plot_x:.2f}" y1="{plot_y + plot_height:.2f}" '
    f'x2="{plot_x + plot_width:.2f}" y2="{plot_y + plot_height:.2f}" '
    f'stroke="{INK_SOFT}" stroke-width="2.5"/>'
)

# X-axis ticks + labels
n_x_ticks = 6
for i in range(n_x_ticks):
    frac = i / (n_x_ticks - 1)
    tick_x = plot_x + frac * plot_width
    tick_y = plot_y + plot_height
    val = frac * 10
    svg_parts.append(
        f'<line x1="{tick_x:.2f}" y1="{tick_y:.2f}" x2="{tick_x:.2f}" y2="{tick_y + 14:.2f}" '
        f'stroke="{INK_SOFT}" stroke-width="2"/>'
    )
    svg_parts.append(
        f'<text x="{tick_x:.2f}" y="{tick_y + 66:.2f}" text-anchor="middle" fill="{INK_SOFT}" '
        f'style="font-size:38px;font-family:{font}">{val:.0f}</text>'
    )

svg_parts.append(
    f'<text x="{plot_x + plot_width / 2:.2f}" y="{plot_y + plot_height + 160:.2f}" '
    f'text-anchor="middle" fill="{INK}" style="font-size:44px;font-family:{font}">'
    f"Distance East (km)</text>"
)

# Y-axis ticks + labels
n_y_ticks = 6
for i in range(n_y_ticks):
    frac = i / (n_y_ticks - 1)
    tick_y = plot_y + plot_height - frac * plot_height
    tick_x = plot_x
    val = frac * 10
    svg_parts.append(
        f'<line x1="{tick_x - 14:.2f}" y1="{tick_y:.2f}" x2="{tick_x:.2f}" y2="{tick_y:.2f}" '
        f'stroke="{INK_SOFT}" stroke-width="2"/>'
    )
    svg_parts.append(
        f'<text x="{tick_x - 26:.2f}" y="{tick_y + 14:.2f}" text-anchor="end" fill="{INK_SOFT}" '
        f'style="font-size:38px;font-family:{font}">{val:.0f}</text>'
    )

y_title_x = plot_x - 200
y_title_y = plot_y + plot_height / 2
svg_parts.append(
    f'<text x="{y_title_x:.2f}" y="{y_title_y:.2f}" text-anchor="middle" fill="{INK}" '
    f'style="font-size:44px;font-family:{font}" '
    f'transform="rotate(-90, {y_title_x:.2f}, {y_title_y:.2f})">Distance North (km)</text>'
)

# Colorbar — right of plot area (vectorized viridis lookup for segment colors)
cb_width = 72
cb_height = int(plot_height * 0.80)
cb_x = plot_x + plot_width + 120
cb_y = plot_y + (plot_height - cb_height) / 2

n_cb_segments = 120
seg_h = cb_height / n_cb_segments
cb_t = np.clip(1.0 - np.arange(n_cb_segments) / (n_cb_segments - 1), 0.0, 1.0)
cb_idx = np.clip(np.searchsorted(VIR_T, cb_t, side="right") - 1, 0, len(VIRIDIS_STOPS) - 2)
cb_span = VIR_T[cb_idx + 1] - VIR_T[cb_idx]
cb_f = np.where(cb_span == 0, 0.0, (cb_t - VIR_T[cb_idx]) / np.where(cb_span == 0, 1, cb_span))
cb_r = (VIR_R[cb_idx] + (VIR_R[cb_idx + 1] - VIR_R[cb_idx]) * cb_f).astype(int)
cb_g = (VIR_G[cb_idx] + (VIR_G[cb_idx + 1] - VIR_G[cb_idx]) * cb_f).astype(int)
cb_b = (VIR_B[cb_idx] + (VIR_B[cb_idx + 1] - VIR_B[cb_idx]) * cb_f).astype(int)
for i in range(n_cb_segments):
    color = f"#{cb_r[i]:02x}{cb_g[i]:02x}{cb_b[i]:02x}"
    seg_y = cb_y + i * seg_h
    svg_parts.append(
        f'<rect x="{cb_x:.2f}" y="{seg_y:.2f}" width="{cb_width}" '
        f'height="{seg_h + 0.6:.2f}" fill="{color}" stroke="none"/>'
    )

svg_parts.append(
    f'<rect x="{cb_x:.2f}" y="{cb_y:.2f}" width="{cb_width}" height="{cb_height}" '
    f'fill="none" stroke="{INK_SOFT}" stroke-width="1.5"/>'
)

n_cb_labels = 6
for i in range(n_cb_labels):
    frac = i / (n_cb_labels - 1)
    val = z_max - (z_max - z_min) * frac
    label_y = cb_y + frac * cb_height + 14
    svg_parts.append(
        f'<text x="{cb_x + cb_width + 20:.2f}" y="{label_y:.2f}" fill="{INK_SOFT}" '
        f'style="font-size:34px;font-family:{font}">{int(round(val))}</text>'
    )

cb_title_x = cb_x + cb_width + 220
cb_title_y = cb_y + cb_height / 2
svg_parts.append(
    f'<text x="{cb_title_x:.2f}" y="{cb_title_y:.2f}" text-anchor="middle" fill="{INK}" '
    f'style="font-size:40px;font-family:{font}" '
    f'transform="rotate(90, {cb_title_x:.2f}, {cb_title_y:.2f})">Elevation (m)</text>'
)

# Title
bg_rect = f'<rect x="0" y="0" width="{CANVAS_W}" height="{CANVAS_H}" fill="{PAGE_BG}" stroke="none"/>'
title_svg = (
    f'<text x="{CANVAS_W / 2:.2f}" y="120" text-anchor="middle" fill="{INK}" '
    f'style="font-size:64px;font-weight:500;font-family:{font}">'
    f"contour-basic · pygal · anyplot.ai</text>"
)

# Inject custom chrome into pygal's graph group BEFORE the plot overlay so
# pygal's peak markers (and their tooltip hit-areas) render on top.
custom_svg = "\n".join([bg_rect, title_svg] + svg_parts)
plot_group_idx = base_svg.find('class="plot"')
if plot_group_idx != -1:
    insert_idx = base_svg.rfind("<g", 0, plot_group_idx)
    output_svg = base_svg[:insert_idx] + custom_svg + "\n" + base_svg[insert_idx:]
else:
    output_svg = base_svg.replace("</svg>", f"{custom_svg}\n</svg>")

cairosvg.svg2png(bytestring=output_svg.encode("utf-8"), write_to=f"plot-{THEME}.png")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>contour-basic · pygal · anyplot.ai</title>
    <style>
        body {{ margin: 0; background: {PAGE_BG}; display: flex;
                justify-content: center; align-items: center; min-height: 100vh; }}
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

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
