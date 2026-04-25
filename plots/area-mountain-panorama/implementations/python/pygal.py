""" anyplot.ai
area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
Library: pygal 3.1.0 | Python 3.14.4
Quality: 87/100 | Created: 2026-04-25
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
SKY_TOP = "#E8C8A0" if THEME == "light" else "#252D40"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"

# Data — Wallis (Valais) summit panorama, ordered W → E
peaks = [
    ("Weisshorn", 12, 4506),
    ("Zinalrothorn", 30, 4221),
    ("Ober Gabelhorn", 45, 4063),
    ("Dent Blanche", 58, 4358),
    ("Dent d'Hérens", 76, 4171),
    ("Matterhorn", 92, 4478),
    ("Breithorn", 120, 4164),
    ("Pollux", 132, 4092),
    ("Castor", 139, 4223),
    ("Liskamm", 152, 4527),
    ("Monte Rosa", 170, 4634),
    ("Strahlhorn", 192, 4190),
    ("Rimpfischhorn", 204, 4199),
    ("Allalinhorn", 215, 4027),
    ("Alphubel", 225, 4206),
    ("Täschhorn", 236, 4491),
    ("Dom", 250, 4545),
]

# Skyline construction
np.random.seed(42)
angle = np.linspace(0, 262, 1200)

# Base ridge: smoothed random walk in the 3000–3700 m belt (foothills + minor cols)
walk = np.cumsum(np.random.randn(len(angle)) * 1.5)
sigma_walk = 14
g = np.arange(-3 * sigma_walk, 3 * sigma_walk + 1)
kernel_walk = np.exp(-(g**2) / (2 * sigma_walk**2))
walk = np.convolve(walk, kernel_walk / kernel_walk.sum(), mode="same")
walk = (walk - walk.min()) / (walk.max() - walk.min())
ridge = 3000 + walk * 700

# Major summits as Gaussian peaks (max-combined for the visible silhouette)
for _, pos, elev in peaks:
    width = 5.5 + (elev - 4000) / 130
    bump = (elev - 2700) * np.exp(-((angle - pos) ** 2) / (2 * width**2))
    ridge = np.maximum(ridge, 2700 + bump)

# Light final smoothing of the combined ridge
sigma_ridge = 0.8
g = np.arange(-3, 4)
kernel_ridge = np.exp(-(g**2) / (2 * sigma_ridge**2))
ridge = np.convolve(ridge, kernel_ridge / kernel_ridge.sum(), mode="same")

# Canvas + plot box
CANVAS_W, CANVAS_H = 4800, 2700
MARGIN_L, MARGIN_R = 220, 120
MARGIN_T, MARGIN_B = 200, 160

Y_FLOOR, Y_CEIL = 2500, 6050
X_MIN, X_MAX = 0, 262

font = "DejaVu Sans, Helvetica, Arial, sans-serif"

# Pygal Style — first colour is brand green; muted foreground used for axis chrome
custom_style = Style(
    background=PAGE_BG,
    plot_background="transparent",
    foreground=INK_SOFT,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND, INK if THEME == "light" else "#F0EFE8"),
    font_family=font,
    title_font_family=font,
    label_font_family=font,
    major_label_font_family=font,
    tooltip_font_family=font,
    tooltip_font_size=30,
    legend_font_size=34,
    stroke_width=2,
    opacity=".95",
    opacity_hover=".75",
    transition="200ms ease-in",
)

# Pygal XY chart with fill=True draws the ridge silhouette as the brand-green
# series. Peak summits are added as a second non-stroked series so pygal
# renders interactive hover dots over each named summit in the HTML export.
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
    xrange=(X_MIN, X_MAX),
    range=(Y_FLOOR, Y_CEIL),
    fill=True,
    show_dots=False,
    stroke_style={"width": 2},
    truncate_label=-1,
)

ridge_data = [{"value": (float(a), float(e))} for a, e in zip(angle, ridge, strict=True)]
chart.add("Skyline", ridge_data)

peak_data = [{"value": (float(pos), float(elev)), "label": f"{name} · {elev:,} m"} for name, pos, elev in peaks]
chart.add("Peaks", peak_data, show_dots=True, dots_size=10, stroke=False, fill=False)

# Render pygal first; back-compute its plot box from the two extreme summit dots
# so post-processed chrome (sky gradient, leader lines, labels) aligns with the
# interactive markers pygal drew.
base_svg = chart.render(is_unicode=True)

dot_re = re.compile(r'<circle cx="([-\d.]+)" cy="([-\d.]+)"[^>]*class="dot')
dots = [(float(cx), float(cy)) for cx, cy in dot_re.findall(base_svg)]
(p1x, p1y) = dots[0]
(p2x, p2y) = dots[-1]
ref_a, ref_b = peaks[0], peaks[-1]
x_scale = (p2x - p1x) / (ref_b[1] - ref_a[1])
x_off = p1x - ref_a[1] * x_scale
y_scale = (p2y - p1y) / (ref_b[2] - ref_a[2])
y_off = p1y - ref_a[2] * y_scale


def to_svg(ax, ay):
    return MARGIN_L + ax * x_scale + x_off, MARGIN_T + ay * y_scale + y_off


plot_x_left, _ = to_svg(X_MIN, Y_CEIL)
plot_x_right, plot_y_bottom = to_svg(X_MAX, Y_FLOOR)
_, plot_y_top = to_svg(X_MIN, Y_CEIL)
plot_w = plot_x_right - plot_x_left
plot_h = plot_y_bottom - plot_y_top

# Sky gradient + custom labels go BEFORE pygal's plot group so the silhouette
# and interactive dots stay on top.
svg_parts = [
    f'<rect x="0" y="0" width="{CANVAS_W}" height="{CANVAS_H}" fill="{PAGE_BG}" stroke="none"/>',
    f"""<defs>
        <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="{SKY_TOP}"/>
            <stop offset="100%" stop-color="{PAGE_BG}"/>
        </linearGradient>
    </defs>""",
    f'<rect x="{plot_x_left:.2f}" y="{plot_y_top:.2f}" '
    f'width="{plot_w:.2f}" height="{plot_h:.2f}" fill="url(#skyGrad)" stroke="none"/>',
]

# Title
svg_parts.append(
    f'<text x="{CANVAS_W / 2:.2f}" y="110" text-anchor="middle" fill="{INK}" '
    f'style="font-size:62px;font-weight:500;font-family:{font}">'
    f"Wallis Alps · area-mountain-panorama · pygal · anyplot.ai</text>"
)

# Y-axis title + tick labels (drawn manually since pygal labels are off)
y_ticks = [3000, 3500, 4000, 4500, 5000, 5500, 6000]
for v in y_ticks:
    _, ty = to_svg(X_MIN, v)
    svg_parts.append(
        f'<text x="{plot_x_left - 28:.2f}" y="{ty + 14:.2f}" text-anchor="end" '
        f'fill="{INK_SOFT}" style="font-size:36px;font-family:{font}">{v:,}</text>'
    )
    svg_parts.append(
        f'<line x1="{plot_x_left:.2f}" y1="{ty:.2f}" x2="{plot_x_right:.2f}" y2="{ty:.2f}" '
        f'stroke="{INK}" stroke-opacity="0.10" stroke-width="1.2"/>'
    )

y_title_x = plot_x_left - 140
y_title_y = plot_y_top + plot_h / 2
svg_parts.append(
    f'<text x="{y_title_x:.2f}" y="{y_title_y:.2f}" text-anchor="middle" fill="{INK}" '
    f'style="font-size:42px;font-family:{font}" '
    f'transform="rotate(-90, {y_title_x:.2f}, {y_title_y:.2f})">Elevation (m)</text>'
)

# Compass bearings on x-axis
compass_ticks = [(10, "W"), (65, "SW"), (120, "S"), (180, "SE"), (245, "E")]
for ang, label in compass_ticks:
    tx, _ = to_svg(ang, Y_FLOOR)
    svg_parts.append(
        f'<text x="{tx:.2f}" y="{plot_y_bottom + 60:.2f}" text-anchor="middle" '
        f'fill="{INK_SOFT}" style="font-size:36px;font-family:{font}">{label}</text>'
    )

# L-shaped frame (left + bottom)
svg_parts.append(
    f'<line x1="{plot_x_left:.2f}" y1="{plot_y_top:.2f}" x2="{plot_x_left:.2f}" y2="{plot_y_bottom:.2f}" '
    f'stroke="{INK_SOFT}" stroke-width="2"/>'
)
svg_parts.append(
    f'<line x1="{plot_x_left:.2f}" y1="{plot_y_bottom:.2f}" x2="{plot_x_right:.2f}" y2="{plot_y_bottom:.2f}" '
    f'stroke="{INK_SOFT}" stroke-width="2"/>'
)

# Peak labels — staggered across three vertical tiers, with thin leader lines.
# Matterhorn is treated as the focal anchor (heavier weight + colour).
LABEL_TIERS = [4870, 5180, 5490]
for i, (name, pos, elev) in enumerate(peaks):
    is_focal = name == "Matterhorn"
    tier_y_data = LABEL_TIERS[i % 3]
    sx, sy_summit = to_svg(pos, elev)
    _, sy_label = to_svg(pos, tier_y_data)

    leader_color = INK if is_focal else INK_SOFT
    leader_op = 0.85 if is_focal else 0.45
    leader_w = 2.0 if is_focal else 1.2

    svg_parts.append(
        f'<line x1="{sx:.2f}" y1="{sy_summit - 6:.2f}" x2="{sx:.2f}" y2="{sy_label + 18:.2f}" '
        f'stroke="{leader_color}" stroke-opacity="{leader_op}" stroke-width="{leader_w}"/>'
    )

    name_size = 34 if is_focal else 28
    elev_size = 26 if is_focal else 22
    name_weight = "700" if is_focal else "600"
    name_color = INK if is_focal else INK_SOFT
    elev_color = INK_SOFT if is_focal else INK_MUTED

    svg_parts.append(
        f'<text x="{sx:.2f}" y="{sy_label:.2f}" text-anchor="middle" fill="{name_color}" '
        f'style="font-size:{name_size}px;font-weight:{name_weight};font-family:{font}">{name}</text>'
    )
    svg_parts.append(
        f'<text x="{sx:.2f}" y="{sy_label + name_size + 6:.2f}" text-anchor="middle" fill="{elev_color}" '
        f'style="font-size:{elev_size}px;font-family:{font}">{elev:,} m</text>'
    )

# Subtitle
svg_parts.append(
    f'<text x="{CANVAS_W / 2:.2f}" y="170" text-anchor="middle" fill="{INK_SOFT}" '
    f'style="font-size:32px;font-family:{font}">'
    f"Sixteen 4 000 m peaks of the Pennine Alps, viewed W → E from a single vantage</text>"
)

custom_svg = "\n".join(svg_parts)

# Inject the custom chrome BEFORE pygal's plot group so the silhouette and
# interactive markers stay layered on top of the sky gradient.
plot_group_idx = base_svg.find('class="plot"')
if plot_group_idx != -1:
    insert_idx = base_svg.rfind("<g", 0, plot_group_idx)
    output_svg = base_svg[:insert_idx] + custom_svg + "\n" + base_svg[insert_idx:]
else:
    output_svg = base_svg.replace("</svg>", f"{custom_svg}\n</svg>")

cairosvg.svg2png(bytestring=output_svg.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=CANVAS_W)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>area-mountain-panorama · pygal · anyplot.ai</title>
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
