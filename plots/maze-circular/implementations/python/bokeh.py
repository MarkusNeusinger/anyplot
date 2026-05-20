"""anyplot.ai
maze-circular: Circular Maze Puzzle
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-05-20
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Maze parameters — difficulty controls ring count
np.random.seed(42)
difficulty = "medium"  # easy=5 rings, medium=7 rings, hard=9 rings
rings_map = {"easy": 5, "medium": 7, "hard": 9}
rings = rings_map[difficulty]
base_sectors = [8, 12, 16, 20, 24, 28, 32, 36, 40]
sectors_per_ring = base_sectors[:rings]

wall_color = INK
wall_width = 5
entry_color = "#009E73"  # Okabe-Ito position 1 (brand green)
goal_color = "#E69F00"  # Okabe-Ito position 5 (orange)

# Build maze cells: (ring, sector) -> {visited, walls}
cells = {}
for r in range(rings):
    n_sec = sectors_per_ring[r]
    for s in range(n_sec):
        cells[(r, s)] = {"visited": False, "walls": {"inner": True, "outer": True, "cw": True, "ccw": True}}

# Iterative recursive backtracking — neighbors computed inline, no helper functions
stack = [(0, 0)]
cells[(0, 0)]["visited"] = True

while stack:
    ring, sector = stack[-1]
    n_sec = sectors_per_ring[ring]

    # Same-ring neighbors (clockwise and counter-clockwise)
    neighbors = [((ring, (sector - 1) % n_sec), "ccw", "cw"), ((ring, (sector + 1) % n_sec), "cw", "ccw")]
    # Inner ring neighbor
    if ring > 0:
        inner_n = sectors_per_ring[ring - 1]
        neighbors.append(((ring - 1, int(sector * inner_n / n_sec)), "inner", "outer"))
    # Outer ring neighbor
    if ring < rings - 1:
        outer_n = sectors_per_ring[ring + 1]
        neighbors.append(((ring + 1, int(sector * outer_n / n_sec)), "outer", "inner"))

    unvisited = [(n, w, ow) for n, w, ow in neighbors if n in cells and not cells[n]["visited"]]

    if unvisited:
        next_cell, wall_to_remove, opp_wall = unvisited[np.random.randint(len(unvisited))]
        cells[(ring, sector)]["walls"][wall_to_remove] = False
        cells[next_cell]["walls"][opp_wall] = False
        cells[next_cell]["visited"] = True
        stack.append(next_cell)
    else:
        stack.pop()

# Open entry gap on outermost ring
entry_sector = 0
cells[(rings - 1, entry_sector)]["walls"]["outer"] = False

# Figure — 2400×2400 square canvas for circular maze
p = figure(
    width=2400,
    height=2400,
    title="maze-circular · python · bokeh · anyplot.ai",
    x_range=(-1.25, 1.25),
    y_range=(-1.25, 1.25),
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
    toolbar_location=None,
    match_aspect=True,
    min_border_bottom=60,
    min_border_left=60,
    min_border_top=130,
    min_border_right=60,
)

# Hide axes, grid, and figure outline
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Title
p.title.text_font_size = "50pt"
p.title.align = "center"
p.title.text_color = INK

# Ring radii from center hub to outer boundary
ring_radii = np.linspace(0.12, 0.95, rings + 1)

# Draw maze walls: outer arc and radial (cw side only avoids double-drawing)
for r in range(rings):
    n_sec = sectors_per_ring[r]
    sector_angle = 2 * np.pi / n_sec
    inner_radius = ring_radii[r]
    outer_radius = ring_radii[r + 1]

    for s in range(n_sec):
        start_angle = s * sector_angle
        end_angle = (s + 1) * sector_angle

        if cells[(r, s)]["walls"]["outer"]:
            arc_pts = np.linspace(start_angle, end_angle, 50)
            p.line(
                outer_radius * np.cos(arc_pts),
                outer_radius * np.sin(arc_pts),
                line_width=wall_width,
                line_color=wall_color,
            )

        if cells[(r, s)]["walls"]["cw"]:
            p.line(
                [inner_radius * np.cos(end_angle), outer_radius * np.cos(end_angle)],
                [inner_radius * np.sin(end_angle), outer_radius * np.sin(end_angle)],
                line_width=wall_width,
                line_color=wall_color,
            )

# Outer boundary circle with entry gap
outer_r = ring_radii[-1]
outer_n = sectors_per_ring[-1]
entry_start_angle = entry_sector * (2 * np.pi / outer_n)
entry_end_angle = (entry_sector + 1) * (2 * np.pi / outer_n)

boundary_pts = np.linspace(entry_end_angle, entry_start_angle + 2 * np.pi, 360)
p.line(outer_r * np.cos(boundary_pts), outer_r * np.sin(boundary_pts), line_width=wall_width + 2, line_color=wall_color)

# Inner boundary (central hub)
theta = np.linspace(0, 2 * np.pi, 120)
p.line(ring_radii[0] * np.cos(theta), ring_radii[0] * np.sin(theta), line_width=wall_width, line_color=wall_color)

# Center goal circle
goal_r = ring_radii[0] * 0.65
p.patch(goal_r * np.cos(theta), goal_r * np.sin(theta), fill_color=goal_color, line_color=wall_color, line_width=3)

p.add_layout(
    Label(x=0, y=-0.01, text="★", text_font_size="28pt", text_align="center", text_baseline="middle", text_color=INK)
)

# Entry triangle marker
entry_angle = (entry_start_angle + entry_end_angle) / 2
entry_x = 1.04 * np.cos(entry_angle)
entry_y = 1.04 * np.sin(entry_angle)
p.scatter(
    [entry_x],
    [entry_y],
    marker="triangle",
    size=30,
    fill_color=entry_color,
    line_color=wall_color,
    angle=entry_angle - np.pi / 2,
)

p.add_layout(
    Label(
        x=entry_x * 1.14,
        y=entry_y * 1.14,
        text="START",
        text_font_size="22pt",
        text_align="center",
        text_baseline="middle",
        text_color=entry_color,
        text_font_style="bold",
    )
)

# Save HTML catalog artifact
output_file(f"plot-{THEME}.html", title="Circular Maze Puzzle")
save(p)

# Screenshot via headless Chrome (Selenium — export_png not available in CI)
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
