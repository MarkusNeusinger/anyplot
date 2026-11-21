"""anyplot.ai
contour-filled: Filled Contour Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-11
"""

import os

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# imprint_div: matte red <-> theme-adaptive midpoint <-> blue, centred on zero
DIV_STOPS = ["#AE3030", PAGE_BG, "#4467A3"]

# Constants
BANDS_PER_SIDE = 8  # levels evenly stepped on each side of the zero midpoint
LEVEL_ROUNDING = 0.05  # the step between levels is a multiple of this

# Columns: set these to your table's column names
X_POS = "X position (a.u.)"  # role: x
Y_POS = "Y position (a.u.)"  # role: y
INTENSITY = "Intensity (a.u.)"  # role: z

# Data: replace this block with your own long table of x, y, z, for example df = pd.read_csv("field.csv")
n_points = 80
grid = np.linspace(-3, 3, n_points)
gx, gy = np.meshgrid(grid, grid)
field = (
    1.5 * np.exp(-((gx - 1) ** 2 + (gy - 1) ** 2))
    - 1.0 * np.exp(-((gx + 1) ** 2 + (gy + 1) ** 2))
    + 0.8 * np.exp(-((gx - 1) ** 2 + (gy + 1.5) ** 2) / 0.5)
    + 0.5 * np.exp(-((gx + 1.5) ** 2 + (gy - 0.5) ** 2) / 0.8)
)
df = pd.DataFrame({X_POS: gx.ravel(), Y_POS: gy.ravel(), INTENSITY: field.ravel()})

# Plot: reads only df and the constants above
table = df.pivot_table(index=Y_POS, columns=X_POS, values=INTENSITY)
xs = table.columns.to_numpy(dtype=float)
ys = table.index.to_numpy(dtype=float)
Z = table.to_numpy(dtype=float)

# Evenly stepped levels, symmetric about zero so the diverging midpoint is a band boundary
peak = float(np.nanmax(np.abs(Z)))
step = np.ceil(peak / BANDS_PER_SIDE / LEVEL_ROUNDING) * LEVEL_ROUNDING
levels = step * np.arange(-BANDS_PER_SIDE, BANDS_PER_SIDE + 1)
limit = levels[-1]


def _hex_to_rgb(color):
    return [int(color[i : i + 2], 16) for i in (1, 3, 5)]


def div_color(value):
    """Map a value in [-limit, limit] onto the imprint_div ramp."""
    t = float(np.clip((value + limit) / (2 * limit), 0, 1)) * (len(DIV_STOPS) - 1)
    k = min(int(t), len(DIV_STOPS) - 2)
    c0, c1 = _hex_to_rgb(DIV_STOPS[k]), _hex_to_rgb(DIV_STOPS[k + 1])
    r, g, b = (round(a + (b_ - a) * (t - k)) for a, b_ in zip(c0, c1, strict=True))
    return f"#{r:02x}{g:02x}{b:02x}"


# Canvas and plot-area geometry (landscape 3200 x 1800)
WIDTH, HEIGHT = 3200, 1800
plot_x, plot_y = 330, 200
plot_w, plot_h = 2300, 1340


def to_px(x, y):
    return (plot_x + (x - xs[0]) / (xs[-1] - xs[0]) * plot_w, plot_y + plot_h - (y - ys[0]) / (ys[-1] - ys[0]) * plot_h)


def clip(poly, level, keep_above):
    """Sutherland-Hodgman clip of a (px, py, z) polygon against z >= level or z <= level."""
    out = []
    for p, q in zip(poly, poly[1:] + poly[:1], strict=True):
        p_in = p[2] >= level if keep_above else p[2] <= level
        q_in = q[2] >= level if keep_above else q[2] <= level
        if p_in != q_in:
            t = (level - p[2]) / (q[2] - p[2])
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, level))
        if q_in:
            out.append(q)
    return out


# Split every grid cell into four triangles around its centre so the linear
# interpolation is symmetric, then clip each triangle to the bands it spans.
band_paths = {}
line_paths = {k: [] for k in range(1, len(levels) - 1)}
for i in range(len(ys) - 1):
    for j in range(len(xs) - 1):
        corners = [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]
        pts = [(*to_px(xs[b], ys[a]), Z[a, b]) for a, b in corners]
        centre = (sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4, sum(p[2] for p in pts) / 4)
        for k in range(4):
            tri = [pts[k], pts[(k + 1) % 4], centre]
            zs = [p[2] for p in tri]
            first = max(int(np.searchsorted(levels, min(zs), side="right")) - 1, 0)
            last = min(int(np.searchsorted(levels, max(zs), side="left")), len(levels) - 1)
            for band in range(first, last):
                poly = clip(clip(tri, levels[band], True), levels[band + 1], False)
                if len(poly) >= 3:
                    d = "M" + "L".join(f"{p[0]:.1f},{p[1]:.1f}" for p in poly) + "Z"
                    band_paths.setdefault(band, []).append(d)
            for lv in range(max(first, 1), min(last, len(levels) - 1)):
                crossings = []
                for p, q in zip(tri, tri[1:] + tri[:1], strict=True):
                    if (p[2] - levels[lv]) * (q[2] - levels[lv]) < 0:
                        t = (levels[lv] - p[2]) / (q[2] - p[2])
                        crossings.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
                if len(crossings) == 2:
                    (x1, y1), (x2, y2) = crossings
                    line_paths[lv].append(f"M{x1:.1f},{y1:.1f}L{x2:.1f},{y2:.1f}")

svg = []

# Filled bands: one path per band, filled with the colour of the band's midpoint value
for band, parts in band_paths.items():
    color = div_color((levels[band] + levels[band + 1]) / 2)
    svg.append(
        f'<path d="{"".join(parts)}" fill="{color}" stroke="{color}" stroke-width="1.5" stroke-linejoin="round"/>'
    )

# Contour lines along the band boundaries, thin so the fill stays the main signal
for parts in line_paths.values():
    if parts:
        svg.append(f'<path d="{"".join(parts)}" fill="none" stroke="{INK}" stroke-width="2" stroke-opacity="0.55"/>')

# Axis frame
svg.append(
    f'<rect x="{plot_x}" y="{plot_y}" width="{plot_w}" height="{plot_h}" '
    f'fill="none" stroke="{INK_SOFT}" stroke-width="2.5"/>'
)

# Ticks and tick labels, positions derived from the data extent
for frac in np.linspace(0, 1, 7):
    val = xs[0] + frac * (xs[-1] - xs[0])
    tx = plot_x + frac * plot_w
    svg.append(
        f'<line x1="{tx:.1f}" y1="{plot_y + plot_h}" x2="{tx:.1f}" y2="{plot_y + plot_h + 18}" '
        f'stroke="{INK_SOFT}" stroke-width="2.5"/>'
    )
    svg.append(
        f'<text x="{tx:.1f}" y="{plot_y + plot_h + 70}" text-anchor="middle" fill="{INK_SOFT}" '
        f'style="font-size:44px;font-family:sans-serif">{val:.1f}</text>'
    )
for frac in np.linspace(0, 1, 7):
    val = ys[0] + frac * (ys[-1] - ys[0])
    ty = plot_y + plot_h - frac * plot_h
    svg.append(
        f'<line x1="{plot_x - 18}" y1="{ty:.1f}" x2="{plot_x}" y2="{ty:.1f}" stroke="{INK_SOFT}" stroke-width="2.5"/>'
    )
    svg.append(
        f'<text x="{plot_x - 30}" y="{ty + 15:.1f}" text-anchor="end" fill="{INK_SOFT}" '
        f'style="font-size:44px;font-family:sans-serif">{val:.1f}</text>'
    )

# Axis titles from the column constants
svg.append(
    f'<text x="{plot_x + plot_w / 2}" y="{plot_y + plot_h + 150}" text-anchor="middle" fill="{INK}" '
    f'style="font-size:56px;font-family:sans-serif">{X_POS}</text>'
)
ytx, yty = plot_x - 200, plot_y + plot_h / 2
svg.append(
    f'<text x="{ytx}" y="{yty}" text-anchor="middle" fill="{INK}" '
    f'style="font-size:56px;font-family:sans-serif" transform="rotate(-90, {ytx}, {yty})">{Y_POS}</text>'
)

# Discrete colour bar: one block per band, same levels as the fill
cb_x, cb_w = plot_x + plot_w + 80, 70
cb_h = plot_h * 0.9
cb_y = plot_y + (plot_h - cb_h) / 2
block_h = cb_h / (len(levels) - 1)
for band in range(len(levels) - 1):
    color = div_color((levels[band] + levels[band + 1]) / 2)
    by = cb_y + cb_h - (band + 1) * block_h
    svg.append(
        f'<rect x="{cb_x}" y="{by:.1f}" width="{cb_w}" height="{block_h + 1:.1f}" fill="{color}" stroke="{color}" stroke-width="1"/>'
    )
svg.append(
    f'<rect x="{cb_x}" y="{cb_y:.1f}" width="{cb_w}" height="{cb_h:.1f}" fill="none" stroke="{INK_SOFT}" stroke-width="2.5"/>'
)
for k in range(0, len(levels), 2):
    ly = cb_y + cb_h - k * block_h
    svg.append(
        f'<line x1="{cb_x + cb_w}" y1="{ly:.1f}" x2="{cb_x + cb_w + 14}" y2="{ly:.1f}" stroke="{INK_SOFT}" stroke-width="2.5"/>'
    )
    svg.append(
        f'<text x="{cb_x + cb_w + 24}" y="{ly + 14:.1f}" fill="{INK_SOFT}" '
        f'style="font-size:40px;font-family:sans-serif">{levels[k]:.2f}</text>'
    )
svg.append(
    f'<text x="{cb_x + cb_w / 2}" y="{cb_y - 40:.1f}" text-anchor="middle" fill="{INK}" '
    f'style="font-size:44px;font-family:sans-serif">Intensity</text>'
)

# Style
title = "contour-filled · python · pygal · anyplot.ai"
style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    font_family="sans-serif",
)
chart = pygal.XY(
    width=WIDTH,
    height=HEIGHT,
    style=style,
    title=title,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
)
# pygal draws the title and canvas; the field itself is injected as SVG below
chart.add("", [(0, 0)])
base_svg = chart.render(is_unicode=True)
output_svg = base_svg.replace("</svg>", "\n".join(svg) + "\n</svg>")

# Save
cairosvg.svg2png(bytestring=output_svg.encode("utf-8"), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: {PAGE_BG}; }}
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
    )
