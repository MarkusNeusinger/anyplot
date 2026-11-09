""" anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: pygal 3.1.3 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-08
"""

import os

import numpy as np
import pandas as pd
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

# Columns: set these to your table's column names, rows in path order
X = "X"  # role: x
Y = "Y"  # role: y
Z = "Z"  # role: z
TIME = "Elapsed time (model time units)"  # role: color

# Data: Lorenz attractor trajectory (deterministic chaotic ODE, no randomness);
# replace this block with your own table, for example df = pd.read_csv("trajectory.csv")
sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
times = np.linspace(0.0, 30.0, 4000)  # 0.0075 time units per point keeps the fast outer loops smooth
solution = solve_ivp(
    lambda t, s: [sigma * (s[1] - s[0]), s[0] * (rho - s[2]) - s[1], s[0] * s[1] - beta * s[2]],
    (times[0], times[-1]),
    [0.0, 1.0, 1.05],
    t_eval=times,
    rtol=1e-9,
    atol=1e-9,
)
df = pd.DataFrame({X: solution.y[0], Y: solution.y[1], Z: solution.y[2], TIME: solution.t})

# Plot: orthographic view from elevation 20°, azimuth -45° (world x, y, z → screen u, v), so the
# two wings sit side by side; pygal has no 3D chart type, so axes and ticks are projected the same way
trajectory = df[[X, Y, Z]].to_numpy(dtype=float)
elapsed = df[TIME].to_numpy(dtype=float)
num_points = len(df)
ELEV, AZIM = np.radians(20), np.radians(-45)
PROJ = np.array(
    [[np.cos(AZIM), -np.sin(AZIM), 0.0], [np.sin(AZIM) * np.sin(ELEV), np.cos(AZIM) * np.sin(ELEV), np.cos(ELEV)]]
)
screen = trajectory @ PROJ.T  # a row with a missing value projects to NaN and breaks the line there

# Box around the path in world units; X and Y run along its front floor edges, Z up its left corner.
# One shared tick step (1, 2 or 5 × 10^k) for at most eight ticks on the longest axis keeps the box at equal scale
lo_world, hi_world = np.nanmin(trajectory, axis=0), np.nanmax(trajectory, axis=0)
span = (hi_world - lo_world).max()
raw_step = (span if span > 0 else 1.0) / 8  # a single point still gets a unit box
magnitude = 10 ** np.floor(np.log10(raw_step))
TICK = magnitude * min((m for m in (1, 2, 5, 10) if m * magnitude >= raw_step))
(x0, y0, z0), (x1, y1, z1) = np.floor(lo_world / TICK) * TICK, np.ceil(hi_world / TICK) * TICK
tick_len = 0.03 * (x1 - x0 + y1 - y0)
gap = 2.8 * tick_len
out_x, out_y = np.array([0.0, -1.0, 0.0]), np.array([1.0, 0.0, 0.0])  # outward from the X and Y edges
out_z = np.array([-1.0, -1.0, 0.0]) / np.sqrt(2)  # outward from the left corner, straight left on screen
x_ticks, y_ticks, z_ticks = (np.arange(a, b + TICK / 2, TICK) for a, b in ((x0, x1), (y0, y1), (z0, z1)))

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
    # floor-edge labels sit farther out than Z's, so X's first label drops clear below the Z column
    [(np.array((t, y0, z0)) + 1.7 * gap * out_x, f"{t:g}") for t in x_ticks]
    + [(np.array((x1, t, z0)) + 1.7 * gap * out_y, f"{t:g}") for t in y_ticks]
    + [(np.array((x0, y0, t)) + gap * out_z, f"{t:g}") for t in z_ticks]
    + [(np.array(((x0 + x1) / 2, y0, z0)) + 3.0 * gap * out_x, X)]
    + [(np.array((x1, (y0 + y1) / 2, z0)) + 3.0 * gap * out_y, Y)]
    + [(np.array((x0, y0, z1)) + np.array((0.0, 0.0, 1.4 * gap)), Z)]
)
text_screen = np.array([p for p, _ in text_world], dtype=float) @ PROJ.T

# Canvas: equal screen units per pixel on both axes so the projection is not stretched.
# pygal reserves `margin` on every side and `spacing + title_font_size` for the title, and pads
# the plot box by 2% of each range
WIDTH, HEIGHT, MARGIN, SPACING = 3200, 1800, 60, 30
TITLE_FS, LABEL_FS = 66, 44
extent = np.vstack([screen, text_screen])
pad = np.array([0.06, 0.03]) * (np.nanmax(extent, axis=0) - np.nanmin(extent, axis=0))
lo, hi = np.nanmin(extent, axis=0) - pad, np.nanmax(extent, axis=0) + pad
view_w, view_h = WIDTH - 2 * MARGIN, HEIGHT - 2 * MARGIN - (SPACING + TITLE_FS)
px_per_unit = min(view_w / (hi[0] - lo[0]), view_h / (hi[1] - lo[1])) / 1.04
center = (lo + hi) / 2
half = np.array([view_w, view_h]) / px_per_unit / 2 / 1.04

# Time key in the top right corner: a bar drawn in the line's own gradient, with its end values
num_segments = 30
key_len, key_top = 0.16 * 2 * half[0], center[1] + 0.9 * half[1]
key_x = np.linspace(center[0] + 0.85 * half[0] - key_len, center[0] + 0.85 * half[0], num_segments + 1)
key_text = [
    ((key_x[0] + key_x[-1]) / 2, key_top, TIME),
    (key_x[0], key_top - 2 * LABEL_FS / px_per_unit, f"{np.nanmin(elapsed):.3g}"),
    (key_x[-1], key_top - 2 * LABEL_FS / px_per_unit, f"{np.nanmax(elapsed):.3g}"),
]
key_y = key_top - 1.0 * LABEL_FS / px_per_unit

# pygal prints a point's label value_font_size px right of it and 4/3 value_font_size px below it;
# with value_font_size at 0.26 x the label size the centred text sits on its anchor
shift = np.array([-0.26 * LABEL_FS, 0.0]) / px_per_unit
labels = [{"value": tuple(p + shift), "label": text} for p, (_, text) in zip(text_screen, text_world, strict=True)]
labels += [{"value": (x + shift[0], y), "label": text} for x, y, text in key_text]

# imprint_seq gradient along time (brand green → blue): the path is split into segments of equal
# point count that share their end points, so the line stays continuous; each segment's colour also
# paints its step of the key bar. A point with a missing value becomes None, a break in the line
stops = np.array([[int(h[i : i + 2], 16) for i in (1, 3, 5)] for h in (IMPRINT_PALETTE[0], IMPRINT_PALETTE[2])])
bounds = np.linspace(0, num_points - 1, num_segments + 1).round().astype(int)
segments, gradient_colors = [], []
for i in range(num_segments):
    r, g, b = np.round(stops[0] + (stops[1] - stops[0]) * i / (num_segments - 1)).astype(int)
    gradient_colors.append(f"rgba({r}, {g}, {b}, 0.85)")
    path = [tuple(p) if np.isfinite(p).all() else None for p in screen[bounds[i] : bounds[i + 1] + 1]]
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
    chart.add(
        f"t = {elapsed[bounds[i]]:.3g}–{elapsed[bounds[i + 1]]:.3g}", path, show_dots=False, allow_interruptions=True
    )

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
