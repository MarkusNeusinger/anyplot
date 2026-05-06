""" anyplot.ai
ternary-basic: Basic Ternary Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 93/100 | Created: 2026-05-06
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Soil composition samples (Sand, Silt, Clay)
np.random.seed(42)
n_points = 50

# Generate random compositions that sum to 100%
raw = np.random.dirichlet(alpha=[2, 2, 2], size=n_points) * 100
sand = raw[:, 0]
silt = raw[:, 1]
clay = raw[:, 2]


# Convert ternary coordinates to Cartesian (equilateral triangle)
def ternary_to_cartesian(a, b, c):
    """Convert ternary coordinates (a, b, c) to Cartesian (x, y).
    Triangle vertices: bottom-left (1,0,0), bottom-right (0,1,0), top (0,0,1)
    """
    total = a + b + c
    b_norm = b / total
    c_norm = c / total
    x = 0.5 * (2 * b_norm + c_norm)
    y = (np.sqrt(3) / 2) * c_norm
    return x, y


# Convert data points
x_data, y_data = ternary_to_cartesian(sand, silt, clay)

# Triangle vertices (in Cartesian coordinates)
tri_x = [0, 1, 0.5, 0]
tri_y = [0, 0, np.sqrt(3) / 2, 0]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="Soil Composition · ternary-basic · bokeh · anyplot.ai",
    x_range=(-0.15, 1.15),
    y_range=(-0.15, 1.05),
    tools="",
    toolbar_location=None,
)

# Theme styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Remove default axes
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Draw triangle outline
p.line(tri_x, tri_y, line_width=3, color=INK_SOFT)

# Draw grid lines at 20% intervals
grid_color = INK_SOFT
grid_alpha = 0.15
grid_width = 1.5

for pct in [20, 40, 60, 80]:
    frac = pct / 100

    # Lines parallel to each side
    a1, b1, c1 = frac, 1 - frac, 0
    a2, b2, c2 = frac, 0, 1 - frac
    x1, y1 = ternary_to_cartesian(a1, b1, c1)
    x2, y2 = ternary_to_cartesian(a2, b2, c2)
    p.line([x1, x2], [y1, y2], line_width=grid_width, color=grid_color, alpha=grid_alpha)

    a1, b1, c1 = 1 - frac, frac, 0
    a2, b2, c2 = 0, frac, 1 - frac
    x1, y1 = ternary_to_cartesian(a1, b1, c1)
    x2, y2 = ternary_to_cartesian(a2, b2, c2)
    p.line([x1, x2], [y1, y2], line_width=grid_width, color=grid_color, alpha=grid_alpha)

    a1, b1, c1 = 1 - frac, 0, frac
    a2, b2, c2 = 0, 1 - frac, frac
    x1, y1 = ternary_to_cartesian(a1, b1, c1)
    x2, y2 = ternary_to_cartesian(a2, b2, c2)
    p.line([x1, x2], [y1, y2], line_width=grid_width, color=grid_color, alpha=grid_alpha)

# Add tick labels along each edge
tick_font_size = "16pt"
tick_offset = 0.04

for pct in [0, 20, 40, 60, 80, 100]:
    frac = pct / 100

    x_tick, y_tick = ternary_to_cartesian(1 - frac, frac, 0)
    label = Label(
        x=x_tick,
        y=y_tick - tick_offset,
        text=f"{int(100 - pct)}",
        text_font_size=tick_font_size,
        text_color=INK_SOFT,
        text_align="center",
        text_baseline="top",
    )
    p.add_layout(label)

    x_tick, y_tick = ternary_to_cartesian(0, 1 - frac, frac)
    label = Label(
        x=x_tick + tick_offset * 0.8,
        y=y_tick + tick_offset * 0.5,
        text=f"{int(100 - pct)}",
        text_font_size=tick_font_size,
        text_color=INK_SOFT,
        text_align="left",
        text_baseline="middle",
    )
    p.add_layout(label)

    x_tick, y_tick = ternary_to_cartesian(frac, 0, 1 - frac)
    label = Label(
        x=x_tick - tick_offset * 0.8,
        y=y_tick + tick_offset * 0.5,
        text=f"{int(100 - pct)}",
        text_font_size=tick_font_size,
        text_color=INK_SOFT,
        text_align="right",
        text_baseline="middle",
    )
    p.add_layout(label)

# Add vertex labels
label_font_size = "24pt"
label_offset = 0.08

sand_label = Label(
    x=0 - label_offset,
    y=0 - label_offset,
    text="Sand",
    text_font_size=label_font_size,
    text_font_style="bold",
    text_color=INK,
    text_align="center",
    text_baseline="top",
)
p.add_layout(sand_label)

silt_label = Label(
    x=1 + label_offset,
    y=0 - label_offset,
    text="Silt",
    text_font_size=label_font_size,
    text_font_style="bold",
    text_color=INK,
    text_align="center",
    text_baseline="top",
)
p.add_layout(silt_label)

clay_label = Label(
    x=0.5,
    y=np.sqrt(3) / 2 + label_offset,
    text="Clay",
    text_font_size=label_font_size,
    text_font_style="bold",
    text_color=INK,
    text_align="center",
    text_baseline="bottom",
)
p.add_layout(clay_label)

# Plot data points
source = ColumnDataSource(data={"x": x_data, "y": y_data, "sand": sand, "silt": silt, "clay": clay})

p.scatter(x="x", y="y", source=source, size=20, color=BRAND, alpha=0.7, line_color=BRAND, line_width=2)

# Style title
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.title.align = "center"

# Save HTML
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
