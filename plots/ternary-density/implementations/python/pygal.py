"""anyplot.ai
ternary-density: Ternary Density Plot
Library: pygal 3.1.3 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-19
"""

import math
import os
import re

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: density uses the sequential ramp built from its first and third entries
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEQ_LOW, SEQ_HIGH = IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]  # imprint_seq: green -> blue
CONTOUR_COLOR = "#FAF8F1"  # light line, readable on both ramp ends in both themes

# Constants
TOTAL = 100  # components are shares of a constant total
CONTOUR_LEVELS = [0.2, 0.4, 0.6, 0.8]  # fractions of the peak density
GRID_STEPS = [25, 50, 75]  # ternary grid lines and tick labels, in percent

# Columns: set these to your table's column names
SWEET = "Sweet (%)"  # role: component_a
SOUR = "Sour (%)"  # role: component_b
BITTER = "Bitter (%)"  # role: component_c

# Data: replace this block with your own table, for example df = pd.read_csv("flavors.csv")
rng = np.random.default_rng(7)
# Fruit sodas and juices: sweet-led, with a sour edge
sodas = rng.dirichlet([14, 6, 1.6], 320) * TOTAL
# Coffee and dark tea: bitter-led, little sweetness
coffee = rng.dirichlet([2.6, 2.4, 14], 280) * TOTAL
# Chocolate and malt drinks: a ridge along the sweet-bitter edge, almost no sour
cocoa = rng.dirichlet([1, 0.12, 1], 260) * TOTAL
cocoa[:, 1] = cocoa[:, 1] * 0.25
cocoa = cocoa / cocoa.sum(axis=1, keepdims=True) * TOTAL
samples = np.vstack([sodas, coffee, cocoa])
df = pd.DataFrame({SWEET: samples[:, 0], SOUR: samples[:, 1], BITTER: samples[:, 2]})

# Plot: ternary -> Cartesian (bottom-left Sweet, bottom-right Sour, top Bitter)
H = math.sqrt(3) / 2
table = df[[SWEET, SOUR, BITTER]].dropna()
shares = table.to_numpy() / table.sum(axis=1).to_numpy()[:, None]
px = shares[:, 1] + shares[:, 2] / 2
py = H * shares[:, 2]
VERTEX = {"left": (0.0, 0.0), "right": (1.0, 0.0), "top": (0.5, H)}


def to_xy(a, b, c):
    """Ternary shares (sweet, sour, bitter) to Cartesian coordinates."""
    return b + c / 2, H * c


# Density on a fine grid, confined to the triangle
res = 180
gx = np.linspace(0, 1, res)
gy = np.linspace(0, H, res)
GX, GY = np.meshgrid(gx, gy)
kde = gaussian_kde(np.vstack([px, py]), bw_method=0.16)
Z = kde(np.vstack([GX.ravel(), GY.ravel()])).reshape(GX.shape)
inside = (GY >= -1e-9) & (GY <= np.sqrt(3) * GX + 1e-9) & (GY <= np.sqrt(3) * (1 - GX) + 1e-9)
Z = np.where(inside, Z, np.nan)
Z_rel = Z / np.nanmax(Z)

# Density raster: imprint_seq from low (green) to high (blue), transparent outside the triangle
lo = np.array([int(SEQ_LOW[i : i + 2], 16) for i in (1, 3, 5)], dtype=float)
hi = np.array([int(SEQ_HIGH[i : i + 2], 16) for i in (1, 3, 5)], dtype=float)
t = np.nan_to_num(Z_rel, nan=0.0)
cell_rgb = (lo + (hi - lo) * t[..., None]).round().astype(int)

# Contours of the same density surface: marching squares, one pygal series per polyline
Zc = np.nan_to_num(Z_rel, nan=0.0)


def level_segments(level):
    """Line segments where the density crosses `level`, interpolated along the grid-cell edges."""
    segments = []
    for i in range(res - 1):
        for j in range(res - 1):
            corners = [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]
            hits = []
            for k in range(4):
                (i0, j0), (i1, j1) = corners[k], corners[(k + 1) % 4]
                v0, v1 = Zc[i0, j0], Zc[i1, j1]
                if (v0 - level) * (v1 - level) < 0:
                    w = (level - v0) / (v1 - v0)
                    hits.append((gx[j0] + w * (gx[j1] - gx[j0]), gy[i0] + w * (gy[i1] - gy[i0])))
            for k in range(0, len(hits) - 1, 2):
                segments.append((hits[k], hits[k + 1]))
    # Chain the segments that share an end point into polylines
    ends = {}
    for n, seg in enumerate(segments):
        for p in seg:
            ends.setdefault((round(p[0], 9), round(p[1], 9)), []).append(n)
    used = [False] * len(segments)
    lines = []
    for n in range(len(segments)):
        if used[n]:
            continue
        used[n] = True
        line = list(segments[n])
        for _ in range(2):  # grow at the tail, then reverse and grow at the other end
            while True:
                tail = (round(line[-1][0], 9), round(line[-1][1], 9))
                nxt = next((m for m in ends[tail] if not used[m]), None)
                if nxt is None:
                    break
                used[nxt] = True
                a, b = segments[nxt]
                line.append(b if (round(a[0], 9), round(a[1], 9)) == tail else a)
            line.reverse()
        lines.append(line)
    return lines


contours = [line for level in CONTOUR_LEVELS for line in level_segments(level * Zc.max())]

# Ternary grid: lines of constant share, parallel to the triangle's sides
grid_lines = []
for s in GRID_STEPS:
    f = s / TOTAL
    grid_lines.append([to_xy(1 - f, 0, f), to_xy(0, 1 - f, f)])  # constant bitter
    grid_lines.append([to_xy(1 - f, f, 0), to_xy(0, f, 1 - f)])  # constant sour
    grid_lines.append([to_xy(f, 0, 1 - f), to_xy(f, 1 - f, 0)])  # constant sweet

# Edge tick labels, each edge naming the component whose grid lines end on it:
# sweet along the bottom, bitter up the left edge, sour down the right edge
tick_points = []
for s in GRID_STEPS:
    f = s / TOTAL
    bx, by = to_xy(f, 1 - f, 0)
    lx, ly = to_xy(1 - f, 0, f)
    rx, ry = to_xy(0, f, 1 - f)
    tick_points.append({"value": (bx, by - 0.045), "label": f"{s}%"})
    tick_points.append({"value": (lx - 0.055, ly - 0.012), "label": f"{s}%"})
    tick_points.append({"value": (rx + 0.055, ry - 0.012), "label": f"{s}%"})

# Chart: pygal XY draws the frame, grid, contours and labels
SIZE = 2400
X_PAD, Y_PAD = 0.14, 0.16
XR = (-X_PAD, 1 + X_PAD)
series = (
    [("triangle", [VERTEX["left"], VERTEX["right"], VERTEX["top"], VERTEX["left"]], INK, 4, None)]
    + [("grid", g, INK_SOFT, 3, "12,9") for g in grid_lines]
    + [("contour", line, CONTOUR_COLOR, 3, None) for line in contours]
)
style = Style(
    background=PAGE_BG,
    plot_background="transparent",
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(s[2] for s in series) + (INK_SOFT,),
    title_font_size=54,
    value_font_size=40,
    label_font_size=40,
    major_label_font_size=40,
    legend_font_size=40,
    font_family="sans-serif",
    title_font_family="sans-serif",
    value_font_family="sans-serif",
)


def build(yr):
    chart = pygal.XY(
        width=SIZE,
        height=SIZE,
        style=style,
        title="Beverage Flavor Profiles\nternary-density · python · pygal · anyplot.ai",
        show_legend=False,
        show_x_labels=False,
        show_y_labels=False,
        show_x_guides=False,
        show_y_guides=False,
        show_minor_x_labels=False,
        show_minor_y_labels=False,
        dots_size=0,
        xrange=XR,
        range=yr,
        margin_left=60,
        margin_right=60,
        margin_bottom=60,
        margin_top=40,
        stroke=True,
    )
    for name, pts, _, width, dash in series:
        stroke_style = {"width": width, "linecap": "round", "linejoin": "round"}
        if dash:
            stroke_style["dasharray"] = dash
        chart.add(name, pts, stroke_style=stroke_style, show_dots=False)
    return chart


def calibrate(svg):
    """Pixel position of the triangle's corners inside the plot group, read back from the pygal SVG."""
    plot = re.search(r'<g transform="translate\(([\d.]+), ([\d.]+)\)" class="plot">', svg)
    path = re.search(r'<path d="M([\d. -]+) L([\d. -]+)" class="line reactive nofill"', svg)
    ox, oy = float(plot.group(1)), float(plot.group(2))
    nums = [float(v) for v in (path.group(1) + " " + path.group(2)).split()]
    pts = list(zip(nums[0::2], nums[1::2], strict=True))
    sx = pts[1][0] - pts[0][0]  # pixels per unit along x
    sy = (pts[0][1] - pts[2][1]) / H  # pixels per unit along y
    return ox, oy, pts[0][0], pts[0][1], sx, sy


YR = (-Y_PAD, 1 - Y_PAD)
for _ in range(3):  # equalise the pixel scale of both axes so the triangle is equilateral
    svg = build(YR).render(is_unicode=True)
    ox, oy, x0, y0, sx, sy = calibrate(svg)
    YR = (YR[0], YR[0] + (YR[1] - YR[0]) * sy / sx)
ox, oy, x0, y0, sx, sy = calibrate(svg)


def px_x(x):
    return ox + x0 + x * sx


def px_y(y):
    return oy + y0 - y * sx


def loc_x(x):  # same position inside the translated plot group
    return px_x(x) - ox


def loc_y(y):
    return px_y(y) - oy


# Raster under the series, clipped to the triangle; colorbar and vertex labels on top
tri = " ".join(f"{loc_x(x):.1f},{loc_y(y):.1f}" for x, y in (VERTEX["left"], VERTEX["right"], VERTEX["top"]))
cw = sx / (res - 1)
rects = "".join(
    f'<rect x="{loc_x(gx[j]) - cw / 2:.1f}" y="{loc_y(gy[i]) - cw / 2:.1f}" width="{cw + 0.6:.1f}" height="{cw + 0.6:.1f}" '
    f'fill="rgb({cell_rgb[i, j, 0]},{cell_rgb[i, j, 1]},{cell_rgb[i, j, 2]})" />'
    for i in range(res)
    for j in range(res)
    if inside[i, j]
)
image = f'<clipPath id="tri-clip"><polygon points="{tri}" /></clipPath><g clip-path="url(#tri-clip)">{rects}</g>'
# the first rect of the plot group is the plot background; place the raster right after it
svg = re.sub(
    r'(<g transform="translate\([\d.]+, [\d.]+\)" class="plot">)(<rect[^>]*/>)',
    r"\1\2" + image.replace("\\", "\\\\"),
    svg,
    count=1,
)

cb_w, cb_h = 44, 0.55 * SIZE
cb_x = px_x(1) + 190
cb_y = px_y(H) + 0.1 * SIZE
steps = 60
bar = "".join(
    f'<rect x="{cb_x:.1f}" y="{cb_y + i / steps * cb_h:.1f}" width="{cb_w}" height="{cb_h / steps + 1:.1f}" '
    f'fill="rgb({",".join(str(int(round(v))) for v in lo + (hi - lo) * (1 - i / (steps - 1)))})" />'
    for i in range(steps)
)
ticks = "".join(
    f'<text x="{px_x(p["value"][0]):.1f}" y="{px_y(p["value"][1]) + 14:.1f}" font-size="40" fill="{INK_SOFT}" text-anchor="middle">{p["label"]}</text>'
    for p in tick_points
)
overlay = (
    f'<g font-family="sans-serif" fill="{INK}">'
    f'<text x="{px_x(0) + 60:.1f}" y="{px_y(0) + 110:.1f}" font-size="56" font-weight="bold" text-anchor="middle">{SWEET}</text>'
    f'<text x="{px_x(1) - 60:.1f}" y="{px_y(0) + 110:.1f}" font-size="56" font-weight="bold" text-anchor="middle">{SOUR}</text>'
    f'<text x="{px_x(0.5):.1f}" y="{px_y(H) - 40:.1f}" font-size="56" font-weight="bold" text-anchor="middle">{BITTER}</text>'
    f"{ticks}"
    f'<text x="{cb_x + cb_w / 2:.1f}" y="{cb_y - 30:.1f}" font-size="44" font-weight="bold" text-anchor="middle">Density</text>'
    f"{bar}"
    f'<rect x="{cb_x:.1f}" y="{cb_y:.1f}" width="{cb_w}" height="{cb_h:.1f}" fill="none" stroke="{INK}" stroke-width="2" />'
    f'<text x="{cb_x + cb_w + 14:.1f}" y="{cb_y + 14:.1f}" font-size="36" fill="{INK_SOFT}">High</text>'
    f'<text x="{cb_x + cb_w + 14:.1f}" y="{cb_y + cb_h + 6:.1f}" font-size="36" fill="{INK_SOFT}">Low</text>'
    "</g>"
)
svg = svg.replace("</svg>", overlay + "</svg>")

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png")
