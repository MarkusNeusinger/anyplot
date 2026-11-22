"""anyplot.ai
contour-3d: 3D Contour Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-22
"""

import os
import sys


# Keep the implementation directory (pygal.py, matplotlib.py, ...) from shadowing installed packages
sys.path = [p for p in sys.path if not p.endswith("python")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_LEVELS = 7  # evenly spaced contour levels between the lowest and highest z
VIEW_AZIMUTH = np.radians(-38)  # rotation of the x-y plane around the vertical axis
VIEW_ELEVATION = np.radians(32)  # camera height above the base plane
RELIEF = 0.55  # height of the z range relative to the base edge

# Columns: set these to your table's column names
X = "X coordinate"  # role: x
Y = "Y coordinate"  # role: y
Z = "Height z"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("surface.csv")
grid = np.linspace(-3, 3, 48)
gx, gy = np.meshgrid(grid, grid)
gz = np.exp(-(gx**2 + gy**2) / 2) + 0.3 * np.sin(2 * gx) * np.cos(2 * gy)
df = pd.DataFrame({X: gx.ravel(), Y: gy.ravel(), Z: gz.ravel()})

# Plot: reads only df and the constants above
surface = df.pivot_table(index=Y, columns=X, values=Z, sort=True)
xs, ys = surface.columns.to_numpy(float), surface.index.to_numpy(float)
zs = surface.to_numpy(float)
z_lo, z_hi = np.nanmin(zs), np.nanmax(zs)
levels = np.linspace(z_lo, z_hi, N_LEVELS + 2)[1:-1]
n_levels = len(levels)


def lerp_hex(c0, c1, t):
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(p + (q - p) * t):02X}" for p, q in zip(a, b, strict=True))


# imprint_seq: brand green to blue, one step per contour level
level_colors = [lerp_hex(IMPRINT_PALETTE[0], IMPRINT_PALETTE[2], i / max(n_levels - 1, 1)) for i in range(n_levels)]

x_lo, x_span = xs.min(), np.ptp(xs)
y_lo, y_span = ys.min(), np.ptp(ys)
z_span = z_hi - z_lo


def project(x, y, z):
    """Oblique view: box coordinates in [0, 1] (z scaled by RELIEF) to screen (u, v)."""
    px, py = (np.asarray(x) - x_lo) / x_span - 0.5, (np.asarray(y) - y_lo) / y_span - 0.5
    pz = (np.asarray(z) - z_lo) / z_span * RELIEF
    u = px * np.cos(VIEW_AZIMUTH) - py * np.sin(VIEW_AZIMUTH)
    depth = px * np.sin(VIEW_AZIMUTH) + py * np.cos(VIEW_AZIMUTH)
    return u, depth * np.sin(VIEW_ELEVATION) + pz * np.cos(VIEW_ELEVATION)


def trace(xs, ys, zs, level):
    """Marching squares: the level curves of zs at `level` as polylines (n, 2) in data units."""
    nodes, links = {}, {}  # edge id -> crossing point; edge id -> neighbouring edge ids
    for i in range(len(ys) - 1):
        for j in range(len(xs) - 1):
            corner = ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))
            hit = []
            for k in range(4):
                (a, b), (c, d) = corner[k], corner[(k + 1) % 4]
                za, zb = zs[a, b], zs[c, d]
                if (za - level) * (zb - level) < 0:
                    t = (level - za) / (zb - za)
                    key = (min((a, b), (c, d)), max((a, b), (c, d)))
                    nodes[key] = (xs[b] + t * (xs[d] - xs[b]), ys[a] + t * (ys[c] - ys[a]))
                    hit.append(key)
            pairs = [hit[:2], hit[2:]] if len(hit) == 4 else [hit]
            for pair in pairs:
                if len(pair) == 2:
                    links.setdefault(pair[0], []).append(pair[1])
                    links.setdefault(pair[1], []).append(pair[0])
    lines, seen = [], set()
    # start at open ends first so open curves run end to end, then close the loops
    for start in sorted(links, key=lambda key: (len(links[key]) > 1, key)):
        if start in seen:
            continue
        path, key = [start], start
        seen.add(start)
        while True:
            following = [n for n in links[key] if n not in seen]
            if not following:
                break
            key = following[0]
            seen.add(key)
            path.append(key)
        if len(links[path[-1]]) > 1 and path[0] in links[path[-1]]:
            path.append(path[0])
        lines.append(np.array([nodes[key] for key in path]))
    return [line for line in lines if len(line) > 1]


def pts(u, v):
    return [(float(a), float(b)) for a, b in zip(u, v, strict=True)]


# Series specs in drawing order: (name, points, color, width, opacity)
specs = []

# Base-plane frame and the three axes, with the vertical axis at the left-most corner
corners = [(x_lo, y_lo), (x_lo + x_span, y_lo), (x_lo + x_span, y_lo + y_span), (x_lo, y_lo + y_span)]
cu, cv = project([c[0] for c in corners], [c[1] for c in corners], [z_lo] * 4)
front = int(np.argmin(cv))
left = int(np.argmin(cu))
ring = [(front + k) % 4 for k in range(5)]
specs.append(("base", pts(cu[ring], cv[ring]), INK_MUTED, 6, 0.9))
top_u, top_v = project([corners[left][0]] * 2, [corners[left][1]] * 2, [z_lo, z_hi])
specs.append(("z axis", pts(top_u, top_v), INK_MUTED, 6, 0.9))

# Contours on the base plane (flat, thin) and lifted to their z height (thick)
traced = [trace(xs, ys, zs, lvl) for lvl in levels]
for segs, color in zip(traced, level_colors, strict=True):
    for line in segs:
        u, v = project(line[:, 0], line[:, 1], np.full(len(line), z_lo))
        specs.append((f"base {len(specs)}", pts(u, v), color, 5, 0.45))
for lvl, segs, color in zip(levels, traced, level_colors, strict=True):
    for line in segs:
        u, v = project(line[:, 0], line[:, 1], np.full(len(line), lvl))
        specs.append((f"z = {lvl:.2g}", pts(u, v), color, 12, 1.0))

# Colorbar: one band per level, to the right of the box
bar_u = float(cu.max()) + 0.16
bar_lo, bar_hi = float(cv.min()) + 0.04, float(top_v.max()) - 0.02
edges = np.linspace(z_lo, z_hi, n_levels + 1)
for i, color in enumerate(level_colors):
    v0 = bar_lo + (edges[i] - z_lo) / z_span * (bar_hi - bar_lo)
    v1 = bar_lo + (edges[i + 1] - z_lo) / z_span * (bar_hi - bar_lo)
    specs.append((f"bar {i}", [(bar_u, v0), (bar_u, v1)], color, 90, 1.0))

# Text anchors: invisible series whose point labels carry the axis and colorbar text
labels = []
mid = (corners[front], corners[(front + 1) % 4], corners[(front - 1) % 4])
for (cx, cy), name in ((mid[1], X), (mid[2], Y)):
    ex, ey = (corners[front][0] + cx) / 2, (corners[front][1] + cy) / 2
    u, v = project([ex], [ey], [z_lo])
    away = np.array([u[0], v[0]]) - np.array(
        [project([x_lo + x_span / 2], [y_lo + y_span / 2], [z_lo])[i][0] for i in (0, 1)]
    )
    labels.append({"value": (float(u[0] + away[0] * 0.3 - 0.06), float(v[0] + away[1] * 0.55 - 0.03)), "label": name})
labels.append({"value": (float(top_u[1]), float(top_v[1]) + 0.045), "label": Z})
for tick in (z_lo, z_hi):
    tu, tv = project([corners[left][0]], [corners[left][1]], [tick])
    labels.append({"value": (float(tu[0]) - 0.075, float(tv[0])), "label": f"{tick:.2g}"})
fx, fy = corners[front]
far_x, far_y = 2 * x_lo + x_span - fx, 2 * y_lo + y_span - fy  # the end of each edge away from the front corner
for tx, ty in ((far_x, fy), (fx, far_y)):
    tu, tv = project([tx], [ty], [z_lo])
    tick = tx if ty == fy else ty
    labels.append({"value": (float(tu[0]), float(tv[0]) - 0.05), "label": f"{tick:g}"})
for lvl in levels[:: max(1, n_levels // 4)]:
    v = bar_lo + (lvl - z_lo) / z_span * (bar_hi - bar_lo)
    labels.append({"value": (bar_u + 0.1, v - 0.012), "label": f"{lvl:.2g}"})
labels.append({"value": (bar_u, bar_hi + 0.06), "label": Z})
pad = [(bar_u + 0.2, bar_lo)]  # keeps the colorbar text inside the plot area

# Style
title = "contour-3d · python · pygal · anyplot.ai"
style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(s[2] for s in specs) + (PAGE_BG, PAGE_BG),
    opacity="1",
    opacity_hover="1",
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=44,
    value_label_font_size=48,
    value_colors=(INK,) * (len(specs) + 2),
    stroke_width=2.5,
)

# pygal's own `.line` rule outranks the per-series stroke width, so widths and opacities go in as CSS
rules = "".join(
    f".series.serie-{i} .line{{stroke-width:{width} !important;stroke-opacity:{opacity} !important}}"
    for i, (_, _, _, width, opacity) in enumerate(specs)
)

chart = pygal.XY(
    css=["file://style.css", "file://graph.css", f"inline:{rules}"],
    width=3200,
    height=1800,
    title=title,
    style=style,
    show_legend=False,
    show_dots=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    show_minor_x_labels=False,
    show_minor_y_labels=False,
    print_labels=True,
    include_x_axis=False,
    margin=40,
    stroke=True,
)
for name, points, *_ in specs:
    chart.add(name, points)
chart.add("labels", labels, stroke=False, show_dots=True, dots_size=0.1)
chart.add("pad", pad, stroke=False, show_dots=False)

chart.render_to_file(f"plot-{THEME}.svg")
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
