""" anyplot.ai
scatter-3d: 3D Scatter Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-20
"""

import os
import site
import sys

import numpy as np
import pandas as pd


sys.path.insert(0, site.getsitepackages()[0])

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
AZIMUTH = np.radians(38)  # fixed oblique viewpoint: turn about the vertical axis
ELEVATION = np.radians(24)  # and tilt towards the viewer
N_TICKS = 4

# Columns: set these to your table's column names
LENGTH = "Seed length (mm)"  # role: x
WIDTH = "Seed width (mm)"  # role: y
WEIGHT = "Seed weight (mg)"  # role: z
VARIETY = "Variety"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("seeds.csv")
np.random.seed(42)
varieties = {"Sunrise": (6.0, 3.1, 22.0), "Meadow": (7.8, 3.9, 31.0), "Harvest": (9.1, 3.3, 42.0)}
frames = []
for name, (length, width, weight) in varieties.items():
    n = 50
    seed_length = np.random.normal(length, 0.45, n)
    seed_width = np.random.normal(width, 0.22, n)
    seed_weight = weight + 4.0 * (seed_length - length) + np.random.normal(0, 2.2, n)
    frames.append(pd.DataFrame({LENGTH: seed_length, WIDTH: seed_width, WEIGHT: seed_weight, VARIETY: name}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
axes_cols = [LENGTH, WIDTH, WEIGHT]
lo = df[axes_cols].min().to_numpy()
hi = df[axes_cols].max().to_numpy()
pad = (hi - lo) * 0.06
lo, hi = lo - pad, hi + pad


def unit(points):
    return (np.asarray(points, dtype=float) - lo) / (hi - lo)


def project(u):
    """Orthographic projection of unit-cube coordinates to (screen x, screen y, depth)."""
    u = np.atleast_2d(u)
    c, s = np.cos(AZIMUTH), np.sin(AZIMUTH)
    depth = s * u[:, 0] + c * u[:, 1]
    sx = c * u[:, 0] - s * u[:, 1]
    sy = u[:, 2] * np.cos(ELEVATION) + depth * np.sin(ELEVATION)
    return sx, sy, depth


def screen(u):
    sx, sy, _ = project(u)
    return list(zip(sx.tolist(), sy.tolist()))


# the floor corner farthest from the viewer anchors the two back walls
corners = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
back = corners[np.argmax(project(np.column_stack([corners, np.zeros(4)]))[2])]
bx, by = back
fx, fy = 1 - bx, 1 - by  # the front corner, opposite the back corner
grid_levels = np.linspace(0, 1, N_TICKS)

grid_lines = []
for g in grid_levels:
    grid_lines.append(screen([[bx, by, g], [fx, by, g]]))  # wall behind the x axis
    grid_lines.append(screen([[bx, by, g], [bx, fy, g]]))  # wall behind the y axis
    grid_lines.append(screen([[g, by, 0], [g, by, 1]]))
    grid_lines.append(screen([[bx, g, 0], [bx, g, 1]]))
    grid_lines.append(screen([[g, 0, 0], [g, 1, 0]]))  # floor grid
    grid_lines.append(screen([[0, g, 0], [1, g, 0]]))
frame_lines = [
    screen([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 0]]),  # floor outline
    screen([[bx, by, 0], [bx, by, 1]]),  # back vertical edge
    screen([[fx, by, 1], [bx, by, 1], [bx, fy, 1]]),  # top edges of the back walls
]

# Axis edges sit on the open front of the floor: x runs along y=fy, y along x=fx, z on the front-left vertical
x_edge_y, y_edge_x = fy, fx
tick_labels = []
for g in grid_levels:
    (px, py), *_ = screen([[g, x_edge_y, 0]])
    tick_labels.append(((px, py - 0.07), f"{lo[0] + g * (hi[0] - lo[0]):.1f}"))
    if g != 0:  # the front corner already carries the x axis start
        (px, py), *_ = screen([[y_edge_x, g, 0]])
        tick_labels.append(((px, py - 0.07), f"{lo[1] + g * (hi[1] - lo[1]):.1f}"))
    z_corner = [0 if bx == 1 else 1, by, g]
    (px, py), *_ = screen([[z_corner[0], z_corner[1], g]])
    tick_labels.append(((px - 0.06, py), f"{lo[2] + g * (hi[2] - lo[2]):.0f}"))
axis_titles = [
    (screen([[0.5, x_edge_y, 0]])[0], LENGTH, (0.0, -0.17)),
    (screen([[y_edge_x, 0.5, 0]])[0], WIDTH, (0.0, -0.17)),
    (screen([[1 - bx, by, 0.5]])[0], WEIGHT, (-0.26, 0.0)),
]

# Style
n_groups = df[VARIETY].nunique()
chrome_colors = (INK_MUTED, INK_SOFT, INK_SOFT)
style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE[:n_groups]) + (INK_MUTED,) * len(grid_lines) + (INK_SOFT,) * 40,
    title_font_size=60,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=48,
    value_font_size=44,
    value_colors=(INK_SOFT,),
    opacity=0.72,
    opacity_hover=1.0,
    stroke_width=3,
)

chart = pygal.XY(
    width=2400,
    height=2400,
    style=style,
    title="scatter-3d · python · pygal · anyplot.ai",
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    show_minor_x_labels=False,
    show_minor_y_labels=False,
    legend_at_bottom=True,
    legend_box_size=34,
    dots_size=11,
    stroke=False,
    print_labels=True,
    print_values=False,
    css=[
        "file://style.css",
        "file://graph.css",
        f"inline:.text-overlay .label {{text-anchor: middle; font-size: 44px !important; fill: {INK} !important}}",
    ],
    x_title=None,
    margin_top=30,
    margin_bottom=40,
    include_x_axis=False,
    show_x_axis_line=False,
    truncate_legend=-1,
)
chart.xrange = (-1.0, 0.98)
chart.range = (-0.12, 1.42)

# one series per variety: each marker sits at its own projected x, y, z value
for name, group in df.groupby(VARIETY, sort=False):
    sx, sy, _ = project(unit(group[axes_cols].to_numpy()))
    chart.add(name, list(zip(sx.tolist(), sy.tolist())))

# 3D frame: pane grid and box edges (series without a legend entry)
for line in grid_lines:
    chart.add(None, line, stroke=True, fill=False, show_dots=False, stroke_style={"width": 1.5, "dasharray": "6,10"})
for line in frame_lines:
    chart.add(None, line, stroke=True, fill=False, show_dots=False, stroke_style={"width": 3.5})

# tick values and axis titles ride on invisible points as printed labels
chart.add(
    None,
    [{"value": pos, "label": text} for pos, text in tick_labels],
    stroke=False,
    dots_size=0.01,
    print_labels=True,
    print_values=False,
)
for (px, py), text, (dx, dy) in axis_titles:
    chart.add(
        None,
        [{"value": (px + dx, py + dy), "label": text}],
        stroke=False,
        dots_size=0.01,
        print_labels=True,
        print_values=False,
    )

# Save
chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
