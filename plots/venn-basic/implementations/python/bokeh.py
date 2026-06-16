""" anyplot.ai
venn-basic: Venn Diagram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-11
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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for three sets
OI_COLORS = ["#009E73", "#C475FD", "#4467A3"]

# Data - Three sets representing product feature categories
set_labels = ["Product A", "Product B", "Product C"]
set_sizes = [100, 80, 60]

# Calculate region sizes
only_a = 100 - 30 - 20 + 10  # 60
only_b = 80 - 30 - 25 + 10  # 35
only_c = 60 - 20 - 25 + 10  # 25
only_ab = 30 - 10  # 20
only_ac = 20 - 10  # 10
only_bc = 25 - 10  # 15
abc = 10

# Circle parameters for 3-set Venn diagram
radius = 0.35
centers = [
    (-0.2, 0.15),  # A - top left
    (0.2, 0.15),  # B - top right
    (0.0, -0.2),  # C - bottom center
]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="venn-basic · bokeh · anyplot.ai",
    x_range=(-1, 1),
    y_range=(-0.8, 0.8),
    toolbar_location=None,
)

# Draw three circles
n_points = 100
theta = np.linspace(0, 2 * np.pi, n_points)

for i, (cx, cy) in enumerate(centers):
    x_pts = (cx + radius * np.cos(theta)).tolist()
    y_pts = (cy + radius * np.sin(theta)).tolist()
    p.patch(
        x_pts, y_pts, fill_color=OI_COLORS[i], fill_alpha=0.35, line_color=OI_COLORS[i], line_width=3, line_alpha=0.8
    )

# Add set labels and sizes
label_positions = [
    (-0.55, 0.50, set_labels[0], f"n={set_sizes[0]}"),
    (0.55, 0.50, set_labels[1], f"n={set_sizes[1]}"),
    (0.0, -0.62, set_labels[2], f"n={set_sizes[2]}"),
]

for lx, ly, text, size_text in label_positions:
    label = Label(
        x=lx,
        y=ly,
        text=text,
        text_font_size="32pt",
        text_font_style="bold",
        text_align="center",
        text_baseline="middle",
        text_color=INK,
    )
    p.add_layout(label)

    size_label = Label(
        x=lx,
        y=ly - 0.08,
        text=size_text,
        text_font_size="24pt",
        text_align="center",
        text_baseline="middle",
        text_color=INK_SOFT,
    )
    p.add_layout(size_label)

# Add region counts
region_labels = [
    (-0.35, 0.25, str(only_a)),  # Only A
    (0.35, 0.25, str(only_b)),  # Only B
    (0.0, -0.38, str(only_c)),  # Only C
    (0.0, 0.28, str(only_ab)),  # A ∩ B only
    (-0.18, -0.08, str(only_ac)),  # A ∩ C only
    (0.18, -0.08, str(only_bc)),  # B ∩ C only
    (0.0, 0.05, str(abc)),  # A ∩ B ∩ C
]

for rx, ry, count in region_labels:
    count_label = Label(
        x=rx,
        y=ry,
        text=count,
        text_font_size="36pt",
        text_font_style="bold",
        text_align="center",
        text_baseline="middle",
        text_color=INK,
    )
    p.add_layout(count_label)

# Style
p.title.text_font_size = "48pt"
p.title.align = "center"
p.title.text_color = INK

p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

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
