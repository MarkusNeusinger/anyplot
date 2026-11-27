""" anyplot.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: pygal 3.1.3 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-27
"""

import math
import os
import re
import sys
from itertools import pairwise
from pathlib import Path


sys.path = [p for p in sys.path if p != str(Path(__file__).parent)]

import cairosvg  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal as pygal_lib  # noqa: E402
from contourpy import FillType, contour_generator  # noqa: E402
from pygal.style import Style  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: position 4 (ochre) draws the coastlines
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COAST = IMPRINT_PALETTE[3]

# Imprint sequential ramp, fields stops: colored cells fill the plot
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# Constants
ISOBAR_STEP = 4  # hPa between isobars (standard synoptic interval)
MAJOR_EVERY = 2  # every second isobar is drawn heavy and labelled first

# Simplified coastlines of the North Pacific rim, (lon, lat) vertices
COASTLINES = [
    # Japan main islands
    [(130, 31), (131, 33), (130, 34), (132, 34), (135, 35), (137, 37), (140, 38), (141, 40), (141, 43), (145, 44)],
    # Kamchatka + Kuril arc
    [(152, 47), (155, 52), (158, 56), (163, 58), (167, 54), (165, 50), (152, 47)],
    # Aleutian Islands
    [(167, 54), (172, 53), (178, 52), (188, 52), (195, 54), (200, 57), (210, 56), (220, 57), (225, 56)],
    # Alaska
    [(195, 57), (200, 59), (205, 60), (210, 60), (215, 60), (220, 60), (225, 59), (230, 58), (235, 55), (237, 53)],
    # North American west coast
    [(237, 53), (236, 50), (235, 48), (234, 47), (235, 45), (236, 42), (236, 38), (238, 35), (240, 32), (240, 25)],
    # Asian mainland coast
    [
        (120, 22),
        (122, 24),
        (120, 27),
        (121, 30),
        (122, 32),
        (124, 34),
        (127, 37),
        (129, 38),
        (130, 40),
        (130, 43),
        (132, 46),
        (135, 48),
        (138, 48),
        (141, 46),
        (143, 47),
        (147, 48),
        (150, 47),
        (152, 47),
    ],
]


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Columns: set these to your table's column names
LONGITUDE = "Longitude (°E)"  # role: lon
LATITUDE = "Latitude (°N)"  # role: lat
PRESSURE = "Pressure (hPa)"  # role: value

# Data: replace this block with your own grid, for example df = pd.read_csv("pressure_grid.csv")
# North Pacific sea-level pressure on a regular 40 x 40 lon/lat grid
rng = np.random.default_rng(42)
lon_axis = np.linspace(120, 240, 40)
lat_axis = np.linspace(20, 65, 40)
lon_mesh, lat_mesh = np.meshgrid(lon_axis, lat_axis)

# Background gradient (higher in the subtropics), North Pacific High, Aleutian Low, low off Asia
field = 1020 - (lat_mesh - 20) * 0.25
field += 12 * np.exp(-((((lon_mesh - 200) / 25) ** 2) + ((lat_mesh - 35) / 12) ** 2))
field -= 18 * np.exp(-((((lon_mesh - 185) / 20) ** 2) + ((lat_mesh - 53) / 10) ** 2))
field -= 8 * np.exp(-((((lon_mesh - 145) / 15) ** 2) + ((lat_mesh - 45) / 10) ** 2))
field += rng.normal(0, 0.3, field.shape)

df = pd.DataFrame({LONGITUDE: lon_mesh.ravel(), LATITUDE: lat_mesh.ravel(), PRESSURE: field.ravel()})

# Plot
grid = df.pivot_table(index=LATITUDE, columns=LONGITUDE, values=PRESSURE)
lons = grid.columns.to_numpy(dtype=float)
lats = grid.index.to_numpy(dtype=float)
values = grid.to_numpy()

lon_min, lon_max = lons.min(), lons.max()
lat_min, lat_max = lats.min(), lats.max()

levels = np.arange(math.ceil(np.nanmin(values) / ISOBAR_STEP) * ISOBAR_STEP, np.nanmax(values) + 1e-9, ISOBAR_STEP)
band_edges = [np.nanmin(values) - 1, *levels, np.nanmax(values) + 1]
n_bands = len(band_edges) - 1
band_colors = [ramp_color(SEQ_FIELDS, i / (n_bands - 1)) for i in range(n_bands)]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    guide_stroke_dasharray="",
    colors=(INK_MUTED,),
    title_font_size=50,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal_lib.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="North Pacific Pressure Isobars · contour-map-geographic · python · pygal · anyplot.ai",
    x_title=LONGITUDE,
    y_title=LATITUDE,
    show_legend=False,
    stroke=False,
    dots_size=0,
    show_x_guides=True,
    show_y_guides=True,
    explicit_size=True,
    print_values=False,
    xrange=(lon_min, lon_max),
    range=(lat_min, lat_max),
    margin=100,
    margin_top=160,
    margin_bottom=160,
    margin_left=240,
    margin_right=300,
)
chart.add("", [(lon_min, lat_min), (lon_max, lat_max)])
base_svg = chart.render(is_unicode=True)

# Register the overlay on pygal's own axis (the opaque map covers the guides): fit pixel = a * value + b on the tick guides
plot_x, plot_y = map(float, re.search(r'translate\(([\d.]+), ([\d.]+)\)" class="plot"', base_svg).groups())
plot_w, plot_h = map(
    float, re.search(r'class="plot"><rect x="0" y="0" width="([\d.]+)" height="([\d.]+)"', base_svg).groups()
)
x_guides = re.findall(
    r'<path d="M([\d.]+) 0\.000000 v[\d.]+" class="(?:major )?guide line" />.*?<title>([\d.]+)</title>', base_svg
)
y_guides = re.findall(
    r'<path d="M0\.000000 ([\d.]+) h[\d.]+" class="(?:major )?guide line" />.*?<title>([\d.]+)</title>', base_svg
)
x_slope, x_off = np.polyfit([float(v) for _, v in x_guides], [float(p) for p, _ in x_guides], 1)
y_slope, y_off = np.polyfit([float(v) for _, v in y_guides], [float(p) for p, _ in y_guides], 1)


def to_px(lon, lat):
    return plot_x + x_slope * lon + x_off, plot_y + y_slope * lat + y_off


def path_d(rings, close):
    return " ".join(
        "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in (to_px(*pt) for pt in ring)) + (" Z" if close else "")
        for ring in rings
    )


gen_fill = contour_generator(lons, lats, values, fill_type=FillType.OuterCode)
gen_line = contour_generator(lons, lats, values)

svg_parts = [f'<clipPath id="map"><rect x="{plot_x}" y="{plot_y}" width="{plot_w}" height="{plot_h}"/></clipPath>']

# Filled bands between the isobar levels, opaque
for lo, hi, color in zip(band_edges[:-1], band_edges[1:], band_colors, strict=True):
    points, codes = gen_fill.filled(lo, hi)
    for pts, cds in zip(points, codes, strict=True):
        starts = np.flatnonzero(cds == 1).tolist() + [len(cds)]
        rings = [pts[a:b] for a, b in pairwise(starts)]
        svg_parts.append(f'<path d="{path_d(rings, True)}" fill="{color}" fill-rule="evenodd" stroke="none"/>')

# Coastlines above the fill, in their own ochre
svg_parts.append(
    f'<path d="{path_d(COASTLINES, False)}" fill="none" stroke="{COAST}" stroke-width="6" '
    f'stroke-linejoin="round" stroke-linecap="round" clip-path="url(#map)"/>'
)

# Isobars from contourpy: heavy ink every second level, thin soft ink between
lines_by_level = {}
for i, level in enumerate(levels):
    is_major = i % MAJOR_EVERY == 0
    lines_by_level[level] = [ln for ln in gen_line.lines(level) if len(ln) > 1]
    svg_parts.append(
        f'<path d="{path_d(lines_by_level[level], False)}" fill="none" stroke="{INK if is_major else INK_SOFT}" '
        f'stroke-width="{4 if is_major else 2}" stroke-linejoin="round" stroke-linecap="round"/>'
    )

# Isobar labels: each sits on a vertex of its own line, clear of the edges and of earlier labels
label_w, label_h, min_gap = 116, 50, 260
placed = []
order = [lv for i, lv in enumerate(levels) if i % MAJOR_EVERY == 0] + [
    lv for i, lv in enumerate(levels) if i % MAJOR_EVERY
]
for level in order:
    best = None
    for line in lines_by_level[level]:
        px = np.array([to_px(*pt) for pt in line])
        inside = (
            (px[:, 0] > plot_x + 90)
            & (px[:, 0] < plot_x + plot_w - 90)
            & (px[:, 1] > plot_y + 50)
            & (px[:, 1] < plot_y + plot_h - 50)
        )
        for x, y in px[inside]:
            gap = min((math.hypot(x - qx, y - qy) for qx, qy in placed), default=1e9)
            if gap >= min_gap and (best is None or gap > best[0]):
                best = (gap, x, y)
    if best is not None and level % (ISOBAR_STEP * MAJOR_EVERY) == 0:
        _, x, y = best
        placed.append((x, y))
        svg_parts.append(
            f'<rect x="{x - label_w / 2:.1f}" y="{y - label_h / 2:.1f}" width="{label_w}" height="{label_h}" '
            f'fill="{ELEVATED_BG}" stroke="{INK_MUTED}" stroke-width="1" rx="5"/>'
            f'<text x="{x:.1f}" y="{y + 13:.1f}" text-anchor="middle" fill="{INK}" '
            f'style="font-size:38px;font-weight:bold;font-family:sans-serif">{level:.0f}</text>'
        )

# Colorbar: one opaque swatch per band, so it matches the map fills exactly
cb_x = plot_x + plot_w + 60
cb_h = plot_h * 0.72
cb_y = plot_y + (plot_h - cb_h) / 2
seg_h = cb_h / n_bands
for i, color in enumerate(band_colors[::-1]):
    svg_parts.append(
        f'<rect x="{cb_x}" y="{cb_y + i * seg_h:.1f}" width="48" height="{seg_h + 0.5:.1f}" fill="{color}"/>'
    )
svg_parts.append(
    f'<rect x="{cb_x}" y="{cb_y}" width="48" height="{cb_h}" fill="none" stroke="{INK}" stroke-width="2"/>'
)
for i, level in enumerate(levels[::-1]):
    ty = cb_y + (i + 1) * seg_h
    svg_parts.append(
        f'<line x1="{cb_x + 48}" y1="{ty:.1f}" x2="{cb_x + 60}" y2="{ty:.1f}" stroke="{INK}" stroke-width="2"/>'
        f'<text x="{cb_x + 70}" y="{ty + 13:.1f}" fill="{INK}" style="font-size:38px;font-family:sans-serif">'
        f"{level:.0f}</text>"
    )
cb_name, _, cb_unit = PRESSURE.partition(" ")
for k, word in enumerate((cb_name, cb_unit)):
    svg_parts.append(
        f'<text x="{cb_x + 24}" y="{cb_y - 70 + k * 44}" text-anchor="middle" fill="{INK}" '
        f'style="font-size:40px;font-weight:bold;font-family:sans-serif">{word}</text>'
    )

output_svg = base_svg.replace("</svg>", "\n".join(svg_parts) + "\n</svg>")

cairosvg.svg2png(bytestring=output_svg.encode("utf-8"), write_to=f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "w") as f:
    f.write(output_svg)
