""" anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: pygal 3.1.3 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from scipy.spatial import Voronoi


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
X = "X coordinate (units)"  # role: x
Y = "Y coordinate (units)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("seeds.csv")
rng = np.random.default_rng(42)
df = pd.DataFrame({X: rng.uniform(0.5, 10.5, 25), Y: rng.uniform(0.5, 10.5, 25)})

# Plot: reads only df and the constants above
seeds = df[[X, Y]].dropna().to_numpy()
box_lo = np.floor(seeds.min(axis=0) - 0.5)
box_hi = np.ceil(seeds.max(axis=0) + 0.5)


def cell_polygon(i):
    """Cell of seed i: the bounding box cut by the bisector half-plane of every other seed."""
    poly = [(box_lo[0], box_lo[1]), (box_hi[0], box_lo[1]), (box_hi[0], box_hi[1]), (box_lo[0], box_hi[1])]
    for j in range(len(seeds)):
        if j == i:
            continue
        normal = seeds[j] - seeds[i]
        offset = normal @ (seeds[i] + seeds[j]) / 2
        clipped = []
        for k, p in enumerate(poly):
            q = poly[(k + 1) % len(poly)]
            dp, dq = normal @ p - offset, normal @ q - offset
            if dp <= 0:
                clipped.append(p)
            if dp * dq < 0:
                t = dp / (dp - dq)
                clipped.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
        poly = clipped
    return poly


cells = [cell_polygon(i) for i in range(len(seeds))]

# Neighbouring cells get different colors: greedy coloring over the Voronoi ridges
neighbours = {i: set() for i in range(len(seeds))}
for a, b in Voronoi(seeds).ridge_points:
    neighbours[a].add(b)
    neighbours[b].add(a)
slot = {}
for i in range(len(seeds)):
    taken = {slot[n] for n in neighbours[i] if n in slot}
    slot[i] = next(c for c in range(len(IMPRINT_PALETTE)) if c not in taken)
cell_colors = [IMPRINT_PALETTE[slot[i]] for i in range(len(seeds))]


custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    guide_stroke_color=INK_SOFT,
    major_guide_stroke_color=INK_SOFT,
    colors=tuple(cell_colors) + (INK,),
    opacity="0.6",
    opacity_hover="0.75",
    title_font_size=52,
    label_font_size=44,
    major_label_font_size=38,
    legend_font_size=38,
    value_font_size=30,
    stroke_width=3,
    font_family="sans-serif",
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    major_label_font_family="sans-serif",
)
css = [
    "file://style.css",
    "file://graph.css",
    f"inline:.series .line {{ stroke: {INK_SOFT} !important; stroke-width: 3 !important; stroke-opacity: 1 !important; }}",
    f"inline:.series .dot {{ stroke: {PAGE_BG} !important; stroke-width: 5 !important; fill-opacity: 1 !important; }}",
    f"inline:.plot .background {{ stroke: {INK_SOFT}; stroke-width: 3; }}",
]

chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title="voronoi-basic · python · pygal · anyplot.ai",
    x_title=X,
    y_title=Y,
    xrange=(float(box_lo[0]), float(box_hi[0])),
    range=(float(box_lo[1]), float(box_hi[1])),
    show_legend=False,
    show_x_guides=True,
    show_y_guides=True,
    x_labels=list(range(int(box_lo[0]), int(box_hi[0]) + 1, 2)),
    y_labels=list(range(int(box_lo[1]), int(box_hi[1]) + 1, 2)),
    margin=60,
    print_values=False,
    css=css,
)
# pygal fills an XY series down to the axis; close each cell path and fill its own outline instead
chart._self_close = True
chart._fill = lambda values: values

for i, poly in enumerate(cells):
    chart.add(
        f"Cell {i + 1}",
        [{"value": (float(x), float(y)), "label": f"Cell {i + 1}"} for x, y in poly],
        fill=True,
        show_dots=False,
    )
chart.add(
    "Seeds",
    [{"value": (float(x), float(y)), "label": f"({x:.2f}, {y:.2f})"} for x, y in seeds],
    stroke=False,
    show_dots=True,
    dots_size=14,
)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
