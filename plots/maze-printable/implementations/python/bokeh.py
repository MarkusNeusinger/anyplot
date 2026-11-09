"""anyplot.ai
maze-printable: Printable Maze Puzzle
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Imprint palette: start takes position 1 (brand green), goal position 2
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data: maze parameters — change the grid size or the seed for a new puzzle
MAZE_WIDTH = 25  # cells horizontally
MAZE_HEIGHT = 25  # cells vertically
SEED = 42

# Plot: carve the maze with a depth-first search (a spanning tree: exactly one route)
np.random.seed(SEED)
maze = np.zeros((MAZE_HEIGHT * 2 + 1, MAZE_WIDTH * 2 + 1), dtype=int)  # 0 = wall, 1 = passage
visited = np.zeros((MAZE_HEIGHT, MAZE_WIDTH), dtype=bool)
stack = [(0, 0)]
visited[0, 0] = True
maze[1, 1] = 1
directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

while stack:
    cy, cx = stack[-1]
    neighbors = []
    for dy, dx in directions:
        ny, nx = cy + dy, cx + dx
        if 0 <= ny < MAZE_HEIGHT and 0 <= nx < MAZE_WIDTH and not visited[ny, nx]:
            neighbors.append((ny, nx, dy, dx))
    if neighbors:
        ny, nx, dy, dx = neighbors[np.random.randint(len(neighbors))]
        visited[ny, nx] = True
        maze[cy * 2 + 1 + dy, cx * 2 + 1 + dx] = 1
        maze[ny * 2 + 1, nx * 2 + 1] = 1
        stack.append((ny, nx))
    else:
        stack.pop()

# Interior walls as segments along the cell edges (cell row 0 is the top row)
x0, y0, x1, y1 = [], [], [], []
for row in range(MAZE_HEIGHT):
    for col in range(MAZE_WIDTH):
        top = MAZE_HEIGHT - row
        if col < MAZE_WIDTH - 1 and maze[row * 2 + 1, col * 2 + 2] == 0:  # wall to the east
            x0.append(col + 1)
            y0.append(top - 1)
            x1.append(col + 1)
            y1.append(top)
        if row < MAZE_HEIGHT - 1 and maze[row * 2 + 2, col * 2 + 1] == 0:  # wall to the south
            x0.append(col)
            y0.append(top - 1)
            x1.append(col + 1)
            y1.append(top - 1)

# Outer boundary, open at the entrance (top-left cell) and the exit (bottom-right cell)
border_xs = [[1, MAZE_WIDTH, MAZE_WIDTH], [MAZE_WIDTH - 1, 0, 0]]
border_ys = [[MAZE_HEIGHT, MAZE_HEIGHT, 0], [0, 0, MAZE_HEIGHT]]

margin = 0.8  # empty space around the maze, in cells
span = max(MAZE_WIDTH, MAZE_HEIGHT) + 2 * margin
title = "maze-printable · python · bokeh · anyplot.ai"
p = figure(
    width=2400,
    height=2400,
    title=title,
    x_range=(MAZE_WIDTH / 2 - span / 2, MAZE_WIDTH / 2 + span / 2),
    y_range=(MAZE_HEIGHT / 2 - span / 2, MAZE_HEIGHT / 2 + span / 2),
    tools="",
    toolbar_location=None,
    min_border_top=180,
    min_border_bottom=20,
    min_border_left=100,
    min_border_right=100,
)

p.segment(x0=x0, y0=y0, x1=x1, y1=y1, line_color=INK, line_width=9, line_cap="square")
p.multi_line(xs=border_xs, ys=border_ys, line_color=INK, line_width=16, line_cap="square", line_join="miter")

# Start and goal markers in the entrance and exit cells
start_x, start_y = 0.5, MAZE_HEIGHT - 0.5
goal_x, goal_y = MAZE_WIDTH - 0.5, 0.5
p.scatter([start_x], [start_y], marker="circle", size=62, fill_color=IMPRINT_PALETTE[0], line_color=INK, line_width=3)
p.scatter([goal_x], [goal_y], marker="square", size=56, fill_color=IMPRINT_PALETTE[1], line_color=INK, line_width=3)
p.text(
    [start_x, goal_x],
    [start_y, goal_y],
    text=["S", "G"],
    text_font_size="30pt",
    text_font_style="bold",
    text_color="#1A1A17",
    text_align="center",
    text_baseline="middle",
)

# Style: no axes, grid or frame — position is construction here
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.styles = {"background-color": PAGE_BG}  # the page shows through the frame's anti-aliased edge
p.axis.visible = False
p.grid.visible = False
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"

# Save
output_file(f"plot-{THEME}.html", title=title)
save(p)

W, H = 2400, 2400
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
