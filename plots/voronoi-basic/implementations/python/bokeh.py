"""anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-22
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
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
BRAND = "#009E73"  # Imprint position 1

# Imprint palette: cells cycle through all eight positions
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
X = "X Coordinate"  # role: x
Y = "Y Coordinate"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("seeds.csv")
rng = np.random.default_rng(42)
n_points = 20
df = pd.DataFrame({X: rng.uniform(1, 9, n_points), Y: rng.uniform(1, 9, n_points)})

# Plot: reads only df and the constants above
df = df.dropna(subset=[X, Y])  # a seed without both coordinates has no cell
x, y = df[X].to_numpy(), df[Y].to_numpy()
points = np.column_stack([x, y])
n_points = len(df)

# Bounding box for clipping: the seeds' extent, padded and snapped outward
pad = 0.1 * max(np.ptp(x), np.ptp(y))
x_min, x_max = np.floor(x.min() - pad), np.ceil(x.max() + pad)
y_min, y_max = np.floor(y.min() - pad), np.ceil(y.max() + pad)

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
    width=3200,
    height=1800,
    title="voronoi-basic · python · bokeh · anyplot.ai",
    x_axis_label=X,
    y_axis_label=Y,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
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
        cell_color = IMPRINT_PALETTE[idx % len(IMPRINT_PALETTE)]
        p.patch(xs, ys, fill_color=cell_color, fill_alpha=0.5, line_color=INK_SOFT, line_width=2.5)

# Draw seed points prominently
source = ColumnDataSource(df)
p.scatter(X, Y, source=source, size=26, color=BRAND, line_color=PAGE_BG, line_width=4, alpha=0.95)

# Styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_font_size = "50pt"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
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
W, H = 3200, 1800
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
