""" anyplot.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-08
"""

import os
import sys


# Remove current directory from path to avoid importing local pygal.py
sys.path = [p for p in sys.path if not (p == "" or p == "." or p.endswith("implementations/python"))]

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Imprint palette position 1 — wireframe surface color

# Data — a 20x20 grid, the lower end of the spec's range, keeps the see-through mesh open
grid_size = 20
x = np.linspace(-5, 5, grid_size)
y = np.linspace(-5, 5, grid_size)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2))

# Plot: orthographic view from elevation 30°, azimuth 45° (world x, y, z → screen u, v)
ELEV, AZIM = np.radians(30), np.radians(45)
PROJ = np.array(
    [
        [np.cos(AZIM), -np.sin(AZIM), 0.0],
        [np.sin(AZIM) * np.sin(ELEV), np.cos(AZIM) * np.sin(ELEV), np.cos(ELEV)],
    ]
)
z_scale = 0.5 * np.ptp(x) / np.ptp(Z)  # the box is drawn half as tall as it is wide

# Mesh: one polyline per grid row and per grid column, joined into one series with gaps
screen = np.stack([X, Y, Z * z_scale], axis=-1) @ PROJ.T
mesh = []
for line in [*screen, *screen.transpose(1, 0, 2)]:
    mesh += [tuple(p) for p in line] + [None]

# Axes along the front floor edges (X, Y) and up the left corner (Z), just below the surface,
# so their ticks and numbers stay clear of the mesh
x0, x1, y0, y1 = x.min(), x.max(), y.min(), y.max()
z_ticks = np.linspace(Z.min(), Z.max(), 5)
x_ticks = np.linspace(x0, x1, 5)
y_ticks = np.linspace(y0, y1, 5)
z_floor = (Z.min() - 0.25 * np.ptp(Z)) * z_scale
tick_len = 0.04 * np.ptp(x)
corner_out = np.array([-1.0, 1.0, 0.0]) / np.sqrt(2)  # outward from the left corner, straight left on screen

axis_world = [
    [(x0, y0, z_floor), (x1, y0, z_floor)],
    [(x0, y0, z_floor), (x0, y1, z_floor)],
    [(x0, y1, z_floor), (x0, y1, Z.max() * z_scale)],
]
tick_world = (
    [[(t, y0, z_floor), (t, y0 - tick_len, z_floor)] for t in x_ticks]
    + [[(x0, t, z_floor), (x0 - tick_len, t, z_floor)] for t in y_ticks]
    + [[(x0, y1, t * z_scale), np.array((x0, y1, t * z_scale)) + tick_len * corner_out] for t in z_ticks]
)
axes, ticks = [], []
for segments, series in ((axis_world, axes), (tick_world, ticks)):
    for segment in segments:
        series += [tuple(p) for p in np.array(segment, dtype=float) @ PROJ.T] + [None]

# Tick numbers in world units, and axis names further out
gap = 2.6 * tick_len
tick_labels = (
    [((t, y0 - gap, z_floor), f"{t:g}") for t in x_ticks]
    + [((x0 - gap, t, z_floor), f"{t:g}") for t in y_ticks]
    + [(np.array((x0, y1, t * z_scale)) + gap * corner_out, f"{t:.1f}") for t in z_ticks]
)
name_labels = [
    (((x0 + x1) / 2, y0 - 2.4 * gap, z_floor), "X"),
    ((x0 - 2.4 * gap, (y0 + y1) / 2, z_floor), "Y"),
    ((x0, y1, Z.max() * z_scale + 1.6 * gap), "Z = sin(√(X² + Y²))"),
]

# Canvas: equal screen units per pixel on both axes so the projection is not stretched.
# pygal reserves `margin` on every side and `spacing + title_font_size` for the title above the plot.
WIDTH, HEIGHT, MARGIN, SPACING = 3200, 1800, 60, 30
TITLE_FS, LABEL_FS, NAME_FS = 66, 44, 52
title = "wireframe-3d-basic · python · pygal · anyplot.ai"
view_w, view_h = WIDTH - 2 * MARGIN, HEIGHT - 2 * MARGIN - (SPACING + TITLE_FS)
anchors = np.array([np.asarray(p, dtype=float) for p, _ in tick_labels + name_labels]) @ PROJ.T
extent = np.vstack([screen.reshape(-1, 2), anchors])
pad = np.array([0.9, 0.35]) * np.ptp(x) / 10  # room for the label text around its anchor
lo, hi = extent.min(axis=0) - pad, extent.max(axis=0) + pad
px_per_unit = min(view_w / (hi[0] - lo[0]), view_h / (hi[1] - lo[1]))
center = (lo + hi) / 2
half = np.array([view_w, view_h]) / px_per_unit / 2

# pygal prints a point's label value_font_size px right of and 4/3 value_font_size px below the point;
# shift each label point back so the (centered) text sits on its anchor
shift = np.array([-LABEL_FS, (4 / 3) * LABEL_FS - 0.35 * LABEL_FS]) / px_per_unit
label_points = [{"value": tuple(a + shift), "label": text} for a, (_, text) in zip(anchors, tick_labels + name_labels)]
tick_points, name_points = label_points[: len(tick_labels)], label_points[len(tick_labels) :]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=(INK, INK, BRAND, INK_SOFT, INK_SOFT),
    value_colors=(INK, INK, INK, INK, INK),
    opacity=1,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=4,  # the mesh; pygal's .reactive rule outranks a per-series stroke_style width
    title_font_size=TITLE_FS,
    label_font_size=LABEL_FS,
    major_label_font_size=LABEL_FS,
    value_font_size=LABEL_FS,
    value_label_font_size=LABEL_FS,
    tooltip_font_size=36,
)

chart = pygal.XY(
    style=custom_style,
    width=WIDTH,
    height=HEIGHT,
    title=title,
    margin=MARGIN,
    spacing=SPACING,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    xrange=(center[0] - half[0], center[0] + half[0]),
    range=(center[1] - half[1], center[1] + half[1]),
    print_labels=True,
    print_values=False,
    css=(
        "file://style.css",
        "file://graph.css",
        "inline:.text-overlay text.label { text-anchor: middle; }",
        f"inline:.serie-0 text.label {{ font-size: {NAME_FS}px !important; font-weight: bold; }}",
        "inline:.plot_title { font-weight: bold; }",
        "inline:.serie-3 .line, .serie-4 .line { stroke-width: 2.5px !important; }",
    ),
)

# Label series first, so their indices are fixed for the CSS above; text is always drawn on top
chart.add("Axis names", name_points, stroke=False, dots_size=0)
chart.add("Tick values", tick_points, stroke=False, dots_size=0)
chart.add("Surface", mesh, show_dots=False, allow_interruptions=True)
chart.add("Axes", axes, show_dots=False, allow_interruptions=True)
chart.add("Ticks", ticks, show_dots=False, allow_interruptions=True)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
