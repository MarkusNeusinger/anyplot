""" anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: pygal 3.1.3 | Python 3.13.15
Quality: pending | Updated: 2026-08-25
"""

import os

import numpy as np
import pygal
from pygal.style import Style
from scipy.integrate import solve_ivp


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (see prompts/default-style-guide.md "Categorical Palette")
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Data — Lorenz attractor trajectory (deterministic chaotic ODE, no randomness)
sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
t_end, num_points = 30.0, 4000  # 0.0075 time units per point keeps the fast outer loops smooth
solution = solve_ivp(
    lambda t, s: [sigma * (s[1] - s[0]), s[0] * (rho - s[2]) - s[1], s[0] * s[1] - beta * s[2]],
    (0.0, t_end),
    [0.0, 1.0, 1.05],
    t_eval=np.linspace(0.0, t_end, num_points),
    rtol=1e-9,
    atol=1e-9,
)
trajectory = solution.y.T  # columns x, y, z

# Plot: orthographic view from elevation 20°, azimuth -45° (world x, y, z → screen u, v), so the
# two wings sit side by side; pygal has no 3D chart type, so axes and ticks are projected the same way
ELEV, AZIM = np.radians(20), np.radians(-45)
PROJ = np.array(
    [
        [np.cos(AZIM), -np.sin(AZIM), 0.0],
        [np.sin(AZIM) * np.sin(ELEV), np.cos(AZIM) * np.sin(ELEV), np.cos(ELEV)],
    ]
)
screen = trajectory @ PROJ.T

# Box around the path in world units; X and Y run along its front floor edges, Z up its left corner
TICK = 10
(x0, y0, z0), (x1, y1, z1) = np.floor(trajectory.min(axis=0) / TICK) * TICK, np.ceil(trajectory.max(axis=0) / TICK) * TICK
tick_len = 0.03 * (x1 - x0 + y1 - y0)
gap = 2.8 * tick_len
out_x, out_y = np.array([0.0, -1.0, 0.0]), np.array([1.0, 0.0, 0.0])  # outward from the X and Y edges
out_z = np.array([-1.0, -1.0, 0.0]) / np.sqrt(2)  # outward from the left corner, straight left on screen
x_ticks, y_ticks, z_ticks = (np.arange(a, b + 1, TICK) for a, b in ((x0, x1), (y0, y1), (z0, z1)))

axis_world = [[(x0, y0, z0), (x1, y0, z0)], [(x1, y0, z0), (x1, y1, z0)], [(x0, y0, z0), (x0, y0, z1)]]
tick_world = (
    [[(t, y0, z0), np.array((t, y0, z0)) + tick_len * out_x] for t in x_ticks]
    + [[(x1, t, z0), np.array((x1, t, z0)) + tick_len * out_y] for t in y_ticks]
    + [[(x0, y0, t), np.array((x0, y0, t)) + tick_len * out_z] for t in z_ticks]
)
axes, ticks = [], []
for segments, series in ((axis_world, axes), (tick_world, ticks)):
    for segment in segments:
        series += [tuple(p) for p in np.array(segment, dtype=float) @ PROJ.T] + [None]

text_world = (
    [(np.array((t, y0, z0)) + gap * out_x, f"{t:g}") for t in x_ticks]
    + [(np.array((x1, t, z0)) + gap * out_y, f"{t:g}") for t in y_ticks]
    + [(np.array((x0, y0, t)) + gap * out_z, f"{t:g}") for t in z_ticks[1:]]  # the floor corner carries X's
    + [(np.array(((x0 + x1) / 2, y0, z0)) + 2.3 * gap * out_x, "X")]
    + [(np.array((x1, (y0 + y1) / 2, z0)) + 2.3 * gap * out_y, "Y")]
    + [(np.array((x0, y0, z1)) + np.array((0.0, 0.0, 1.4 * gap)), "Z")]
)
text_screen = np.array([p for p, _ in text_world], dtype=float) @ PROJ.T

# Canvas: equal screen units per pixel on both axes so the projection is not stretched.
# pygal reserves `margin` on every side and `spacing + title_font_size` for the title, and pads
# the plot box by 2% of each range
WIDTH, HEIGHT, MARGIN, SPACING = 3200, 1800, 60, 30
TITLE_FS, LABEL_FS = 66, 44
extent = np.vstack([screen, text_screen])
pad = np.array([0.06, 0.03]) * np.ptp(extent, axis=0)
lo, hi = extent.min(axis=0) - pad, extent.max(axis=0) + pad
view_w, view_h = WIDTH - 2 * MARGIN, HEIGHT - 2 * MARGIN - (SPACING + TITLE_FS)
px_per_unit = min(view_w / (hi[0] - lo[0]), view_h / (hi[1] - lo[1])) / 1.04
center = (lo + hi) / 2
half = np.array([view_w, view_h]) / px_per_unit / 2 / 1.04

# Time key in the top right corner: a bar drawn in the line's own gradient, with its end values
num_segments = 30
key_len, key_top = 0.16 * 2 * half[0], center[1] + 0.9 * half[1]
key_x = np.linspace(center[0] + 0.85 * half[0] - key_len, center[0] + 0.85 * half[0], num_segments + 1)
key_text = [
    ((key_x[0] + key_x[-1]) / 2, key_top, "Elapsed time (model time units)"),
    (key_x[0], key_top - 2 * LABEL_FS / px_per_unit, "0"),
    (key_x[-1], key_top - 2 * LABEL_FS / px_per_unit, f"{t_end:g}"),
]
key_y = key_top - 1.0 * LABEL_FS / px_per_unit

# pygal prints a point's label value_font_size px right of it and 4/3 value_font_size px below it;
# with value_font_size at 0.26 x the label size the centred text sits on its anchor
shift = np.array([-0.26 * LABEL_FS, 0.0]) / px_per_unit
labels = [{"value": tuple(p + shift), "label": text} for p, (_, text) in zip(text_screen, text_world, strict=True)]
labels += [{"value": (x + shift[0], y), "label": text} for x, y, text in key_text]

# imprint_seq gradient along time (brand green → blue): the path is split into equal-time segments
# that share their end points, so the line stays continuous; each segment's colour also paints its
# step of the key bar
stops = np.array([[int(h[i : i + 2], 16) for i in (1, 3, 5)] for h in (IMPRINT_PALETTE[0], IMPRINT_PALETTE[2])])
bounds = np.linspace(0, num_points - 1, num_segments + 1).round().astype(int)
segments, gradient_colors = [], []
for i in range(num_segments):
    r, g, b = np.round(stops[0] + (stops[1] - stops[0]) * i / (num_segments - 1)).astype(int)
    gradient_colors.append(f"rgba({r}, {g}, {b}, 0.85)")
    path = [tuple(p) for p in screen[bounds[i] : bounds[i + 1] + 1]]
    segments.append(path + [None, (key_x[i], key_y), (key_x[i + 1], key_y)])

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=(INK, INK_SOFT, INK_SOFT, *gradient_colors),
    value_colors=(INK,) * (3 + num_segments),
    opacity=1,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=3.5,  # the trajectory; axes, ticks and the key bar are set in the css below
    title_font_size=TITLE_FS,
    label_font_size=LABEL_FS,
    major_label_font_size=LABEL_FS,
    value_font_size=round(0.26 * LABEL_FS),
    value_label_font_size=LABEL_FS,
    tooltip_font_size=36,
)

chart = pygal.XY(
    title="line-3d-trajectory · python · pygal · anyplot.ai",
    width=WIDTH,
    height=HEIGHT,
    style=custom_style,
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
        "inline:.serie-1 .line, .serie-2 .line { stroke-width: 2.5px !important; }",
        "inline:.plot_title { font-weight: bold; }",
    ),
)

# Labels first, so their index is fixed for the css above; text is always drawn above the marks
chart.add("Labels", labels, stroke=False, dots_size=0)
chart.add("Axes", axes, show_dots=False, allow_interruptions=True)
chart.add("Ticks", ticks, show_dots=False, allow_interruptions=True)
for i, path in enumerate(segments):
    t_from, t_to = t_end * bounds[i] / (num_points - 1), t_end * bounds[i + 1] / (num_points - 1)
    chart.add(f"t = {t_from:.1f}–{t_to:.1f}", path, show_dots=False, allow_interruptions=True)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
