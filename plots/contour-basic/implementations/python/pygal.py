""" anyplot.ai
contour-basic: Basic Contour Plot
Library: pygal 3.1.0 | Python 3.14.4
Quality: 82/100 | Created: 2026-04-24
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
VIRIDIS = [
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


def viridis_at(t):
    t = max(0.0, min(1.0, t))
    for i in range(len(VIRIDIS) - 1):
        t0, c0 = VIRIDIS[i]
        t1, c1 = VIRIDIS[i + 1]
        if t0 <= t <= t1:
            f = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            r = int(int(c0[1:3], 16) + (int(c1[1:3], 16) - int(c0[1:3], 16)) * f)
            g = int(int(c0[3:5], 16) + (int(c1[3:5], 16) - int(c0[3:5], 16)) * f)
            b = int(int(c0[5:7], 16) + (int(c1[5:7], 16) - int(c0[5:7], 16)) * f)
            return f"#{r:02x}{g:02x}{b:02x}"
    return VIRIDIS[-1][1]


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
MARGIN_L, MARGIN_R = 360, 520
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

# Filled contour — one quad per grid cell, colored by its mean elevation
for i in range(n_points - 1):
    for j in range(n_points - 1):
        cell_val = (elevation[i, j] + elevation[i, j + 1] + elevation[i + 1, j] + elevation[i + 1, j + 1]) / 4
        t = (cell_val - z_min) / (z_max - z_min)
        color = viridis_at(t)
        cx = plot_x + j * cell_w
        cy = plot_y + plot_height - (i + 1) * cell_h
        svg_parts.append(
            f'<rect x="{cx:.2f}" y="{cy:.2f}" width="{cell_w + 0.6:.2f}" '
            f'height="{cell_h + 0.6:.2f}" fill="{color}" stroke="none"/>'
        )

# Marching-squares contour extraction
minor_levels = np.arange(400, 1251, 50)
major_levels = np.arange(400, 1251, 200)


def lerp(v1, v2, lv):
    if abs(v2 - v1) < 1e-10:
        return 0.5
    return (lv - v1) / (v2 - v1)


def march(level):
    lines = []
    for i in range(n_points - 1):
        for j in range(n_points - 1):
            z00, z01 = elevation[i, j], elevation[i, j + 1]
            z10, z11 = elevation[i + 1, j], elevation[i + 1, j + 1]

            case = 0
            if z00 >= level:
                case |= 1
            if z01 >= level:
                case |= 2
            if z11 >= level:
                case |= 4
            if z10 >= level:
                case |= 8
            if case in (0, 15):
                continue

            x0 = plot_x + j * cell_w
            y_bot = plot_y + plot_height - i * cell_h
            y_top = plot_y + plot_height - (i + 1) * cell_h

            left = (x0, y_bot - cell_h * lerp(z00, z10, level))
            right = (x0 + cell_w, y_bot - cell_h * lerp(z01, z11, level))
            top = (x0 + cell_w * lerp(z10, z11, level), y_top)
            bottom = (x0 + cell_w * lerp(z00, z01, level), y_bot)

            if case in (1, 14):
                lines.append((left, bottom))
            elif case in (2, 13):
                lines.append((bottom, right))
            elif case in (3, 12):
                lines.append((left, right))
            elif case in (4, 11):
                lines.append((right, top))
            elif case == 5:
                lines.append((left, top))
                lines.append((bottom, right))
            elif case in (6, 9):
                lines.append((bottom, top))
            elif case in (7, 8):
                lines.append((left, top))
            elif case == 10:
                lines.append((left, bottom))
                lines.append((right, top))
    return lines


# Minor contours (50 m intervals, subtle)
for lvl in minor_levels:
    for (x1, y1), (x2, y2) in march(lvl):
        svg_parts.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{LINE_COLOR}" stroke-width="2" stroke-opacity="0.30"/>'
        )

# Major contours (200 m intervals, emphasized) — collect segments for labeling
major_segments_by_level = {}
for lvl in major_levels:
    segs = march(lvl)
    major_segments_by_level[int(lvl)] = segs
    for (x1, y1), (x2, y2) in segs:
        svg_parts.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{LINE_COLOR}" stroke-width="4" stroke-opacity="{LINE_OPACITY}"/>'
        )


# Contour level labels — place elevation text at the rightmost point of each
# major contour's eastern flank (stable placement avoids label pile-ups near peaks).
# A PAGE_BG halo keeps digits legible against the viridis fill.
def label_anchors(segments, max_labels=2):
    """Return up to `max_labels` well-separated midpoints from the segment list."""
    if not segments:
        return []
    # Build midpoints of every segment, then sample evenly by segment count
    mids = [((x1 + x2) / 2, (y1 + y2) / 2) for (x1, y1), (x2, y2) in segments]
    n = len(mids)
    if n <= max_labels:
        return mids
    step = n / (max_labels + 1)
    return [mids[int(step * (i + 1))] for i in range(max_labels)]


label_font_px = 40
for lvl, segs in major_segments_by_level.items():
    for cx, cy in label_anchors(segs, max_labels=2):
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

# Colorbar — right of plot area
cb_width = 72
cb_height = int(plot_height * 0.80)
cb_x = plot_x + plot_width + 120
cb_y = plot_y + (plot_height - cb_height) / 2

n_cb_segments = 120
seg_h = cb_height / n_cb_segments
for i in range(n_cb_segments):
    t = 1.0 - i / (n_cb_segments - 1)
    color = viridis_at(t)
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
    f"Mountain Terrain · contour-basic · pygal · anyplot.ai</text>"
)

# Inject custom chrome into pygal's graph group BEFORE the plot overlay so
# pygal's peak markers (and their tooltip hit-areas) render on top.
custom_svg = "\n".join([bg_rect, title_svg] + svg_parts)
overlay_marker = '<g transform="translate('
# Locate pygal's first plot group by class
plot_group_idx = base_svg.find('class="plot"')
if plot_group_idx != -1:
    # Back up to the opening '<g'
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
