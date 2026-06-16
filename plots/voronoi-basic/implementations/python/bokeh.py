""" anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from scipy.spatial import Voronoi
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Okabe-Ito palette for Voronoi cells
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - seed points for Voronoi diagram
np.random.seed(42)
n_points = 20
x = np.random.uniform(1, 9, n_points)
y = np.random.uniform(1, 9, n_points)
points = np.column_stack([x, y])

# Bounding box for clipping
x_min, x_max = 0, 10
y_min, y_max = 0, 10

# Add mirrored points outside boundaries to handle infinite regions properly
mirrored = []
for px, py in points:
    mirrored.append([2 * x_min - px, py])
    mirrored.append([2 * x_max - px, py])
    mirrored.append([px, 2 * y_min - py])
    mirrored.append([px, 2 * y_max - py])
all_points = np.vstack([points, mirrored])

# Compute Voronoi diagram
vor = Voronoi(all_points)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="voronoi-basic · bokeh · anyplot.ai",
    x_axis_label="X Coordinate",
    y_axis_label="Y Coordinate",
    x_range=(x_min, x_max),
    y_range=(y_min, y_max),
)

# Draw Voronoi regions for original points only
for idx in range(n_points):
    region_idx = vor.point_region[idx]
    region = vor.regions[region_idx]

    if not region or -1 in region:
        continue

    vertices = [vor.vertices[i] for i in region]

    # Clip polygon to bounding box using Sutherland-Hodgman algorithm
    polygon = list(vertices)
    for edge in ["left", "right", "bottom", "top"]:
        if not polygon:
            break
        clipped = []
        for i in range(len(polygon)):
            curr = polygon[i]
            next_v = polygon[(i + 1) % len(polygon)]
            curr_in = (
                (curr[0] >= x_min if edge == "left" else True)
                and (curr[0] <= x_max if edge == "right" else True)
                and (curr[1] >= y_min if edge == "bottom" else True)
                and (curr[1] <= y_max if edge == "top" else True)
            )
            next_in = (
                (next_v[0] >= x_min if edge == "left" else True)
                and (next_v[0] <= x_max if edge == "right" else True)
                and (next_v[1] >= y_min if edge == "bottom" else True)
                and (next_v[1] <= y_max if edge == "top" else True)
            )
            if curr_in:
                clipped.append(curr)
                if not next_in:
                    x1, y1 = curr
                    x2, y2 = next_v
                    dx, dy = x2 - x1, y2 - y1
                    if edge == "left":
                        t = (x_min - x1) / dx if dx != 0 else 0
                        clipped.append([x_min, y1 + t * dy])
                    elif edge == "right":
                        t = (x_max - x1) / dx if dx != 0 else 0
                        clipped.append([x_max, y1 + t * dy])
                    elif edge == "bottom":
                        t = (y_min - y1) / dy if dy != 0 else 0
                        clipped.append([x1 + t * dx, y_min])
                    elif edge == "top":
                        t = (y_max - y1) / dy if dy != 0 else 0
                        clipped.append([x1 + t * dx, y_max])
            elif next_in:
                x1, y1 = curr
                x2, y2 = next_v
                dx, dy = x2 - x1, y2 - y1
                if edge == "left":
                    t = (x_min - x1) / dx if dx != 0 else 0
                    clipped.append([x_min, y1 + t * dy])
                elif edge == "right":
                    t = (x_max - x1) / dx if dx != 0 else 0
                    clipped.append([x_max, y1 + t * dy])
                elif edge == "bottom":
                    t = (y_min - y1) / dy if dy != 0 else 0
                    clipped.append([x1 + t * dx, y_min])
                elif edge == "top":
                    t = (y_max - y1) / dy if dy != 0 else 0
                    clipped.append([x1 + t * dx, y_max])
        polygon = clipped

    if len(polygon) >= 3:
        xs = [v[0] for v in polygon]
        ys = [v[1] for v in polygon]
        cell_color = IMPRINT[idx % len(IMPRINT)]
        p.patch(xs, ys, fill_color=cell_color, fill_alpha=0.5, line_color=INK_SOFT, line_width=2.5)

# Draw seed points prominently
source = ColumnDataSource(data={"x": x, "y": y})
p.scatter("x", "y", source=source, size=22, color=BRAND, line_color=PAGE_BG, line_width=4, alpha=0.95)

# Styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_font_size = "28pt"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK_SOFT
p.ygrid.grid_line_color = INK_SOFT
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Save
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 4800, 2700
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
