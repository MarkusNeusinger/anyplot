"""anyplot.ai
maze-printable: Printable Maze Puzzle
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#000000" if THEME == "light" else "#F0EFE8"  # walls: black on white for printing

# Imprint palette: the start marker takes position 1
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data: maze parameters, no table (a generated puzzle layout)
MAZE_WIDTH = 25  # cells horizontally
MAZE_HEIGHT = 25  # cells vertically
SEED = 42

# Plot
rng = np.random.default_rng(SEED)

# Depth-first carving: `open_right[y][x]` / `open_down[y][x]` mark removed interior walls
open_right = np.zeros((MAZE_HEIGHT, MAZE_WIDTH), dtype=bool)
open_down = np.zeros((MAZE_HEIGHT, MAZE_WIDTH), dtype=bool)
visited = np.zeros((MAZE_HEIGHT, MAZE_WIDTH), dtype=bool)
visited[0, 0] = True
stack = [(0, 0)]
while stack:
    cy, cx = stack[-1]
    options = [
        (cy + dy, cx + dx)
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0))
        if 0 <= cy + dy < MAZE_HEIGHT and 0 <= cx + dx < MAZE_WIDTH and not visited[cy + dy, cx + dx]
    ]
    if not options:
        stack.pop()
        continue
    ny, nx = options[rng.integers(len(options))]
    if ny == cy:
        open_right[cy, min(cx, nx)] = True
    else:
        open_down[min(cy, ny), cx] = True
    visited[ny, nx] = True
    stack.append((ny, nx))

# Wall runs on the cell-edge lattice; y grows downward, so the maze is drawn with y flipped
interior_runs = []
for y in range(1, MAZE_HEIGHT):  # horizontal interior walls on lattice line y
    x = 0
    while x < MAZE_WIDTH:
        if open_down[y - 1, x]:
            x += 1
            continue
        start = x
        while x < MAZE_WIDTH and not open_down[y - 1, x]:
            x += 1
        interior_runs.append([(start, MAZE_HEIGHT - y), (x, MAZE_HEIGHT - y)])
for x in range(1, MAZE_WIDTH):  # vertical interior walls on lattice line x
    y = 0
    while y < MAZE_HEIGHT:
        if open_right[y, x - 1]:
            y += 1
            continue
        start = y
        while y < MAZE_HEIGHT and not open_right[y, x - 1]:
            y += 1
        interior_runs.append([(x, MAZE_HEIGHT - start), (x, MAZE_HEIGHT - y)])

# Outer boundary, closed except for an entrance in the top-left cell and an exit in the bottom-right cell
boundary_runs = [
    [(1, MAZE_HEIGHT), (MAZE_WIDTH, MAZE_HEIGHT)],  # top, entrance above column 0
    [(0, 0), (MAZE_WIDTH - 1, 0)],  # bottom, exit below the last column
    [(0, 0), (0, MAZE_HEIGHT)],  # left
    [(MAZE_WIDTH, 0), (MAZE_WIDTH, MAZE_HEIGHT)],  # right
]
wall_runs = boundary_runs + interior_runs

# Start and goal markers sit in the centre of their cells
start_cell = (0.5, MAZE_HEIGHT - 0.5)
goal_cell = (MAZE_WIDTH - 0.5, 0.5)
LABEL_SHIFT = 1.04
LABEL_LIFT = 0.8  # pygal anchors value text at its left edge; shift back to centre the letter

# Layout: a square canvas with equal data units per pixel on both axes
CANVAS = 2400
MARGIN = 150
TITLE_SIZE = 56
title_band = 1.0 * TITLE_SIZE  # pygal reserves roughly this height above the plot
side = CANVAS - 2 * MARGIN
margin_top = MARGIN + title_band
plot_side = CANVAS - margin_top - MARGIN
inset = (side - plot_side) / 2 + 26  # 26 px: pygal's own side padding around the plot
cell = plot_side / max(MAZE_WIDTH, MAZE_HEIGHT)
wall_stroke = 0.2 * cell
n_walls = len(wall_runs)

style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=PAGE_BG,
    colors=(INK,) * n_walls + (IMPRINT_PALETTE[0], IMPRINT_PALETTE[4]),
    stroke_width=wall_stroke,
    stroke_width_hover=wall_stroke,
    title_font_size=TITLE_SIZE,
    value_font_size=int(0.75 * cell),
    label_font_size=int(0.6 * cell),
    value_colors=(INK,) * n_walls + (IMPRINT_PALETTE[0], IMPRINT_PALETTE[4]),
    font_family="sans-serif",
    stroke_opacity=1,
    stroke_opacity_hover=1,
    opacity=1,
    opacity_hover=1,
)

chart = pygal.XY(
    width=CANVAS,
    height=CANVAS,
    style=style,
    title="maze-printable · python · pygal · anyplot.ai",
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    show_minor_x_labels=False,
    show_minor_y_labels=False,
    xrange=(0, MAZE_WIDTH),
    range=(0, MAZE_HEIGHT),
    include_x_axis=False,
    stroke=True,
    show_dots=False,
    dots_size=0,
    margin_top=int(margin_top),
    margin_bottom=MARGIN,
    margin_left=int(MARGIN + inset),
    margin_right=int(MARGIN + inset),
    print_values=True,
    tooltip_border_radius=0,
)
for i, run in enumerate(wall_runs):
    chart.add(f"Wall {i}", run, stroke_style={"linecap": "square"}, formatter=lambda _v: "")
for name, (px, py), letter in (("Start", start_cell, "S"), ("Goal", goal_cell, "G")):
    chart.add(
        name,
        [(px - LABEL_SHIFT, py + LABEL_LIFT)],
        stroke=False,
        show_dots=True,
        dots_size=0.01,
        formatter=lambda _v, text=letter: text,
    )

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
