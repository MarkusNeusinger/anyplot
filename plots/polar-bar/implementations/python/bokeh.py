""" anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label, Title
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1 — first series

# Data - Wind frequency by direction (8 compass points)
np.random.seed(42)
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
# Simulating wind pattern: prevailing winds from SW and W
frequencies = np.array([12, 8, 10, 6, 9, 18, 22, 14])

# Convert directions to angles (0° = North, clockwise)
# In Bokeh, angles are counterclockwise from East, so we need to convert
n_dirs = len(directions)
angles = np.linspace(0, 2 * np.pi, n_dirs, endpoint=False)
# Bokeh: 0 = East, pi/2 = North, counterclockwise
start_angles = np.pi / 2 - angles - np.pi / n_dirs
end_angles = np.pi / 2 - angles + np.pi / n_dirs

# Normalize frequencies for bar length
max_freq = frequencies.max()
radii = frequencies / max_freq * 0.75  # Scale to 75% of plot radius

# Colors - Use Okabe-Ito palette (first series is brand green)
IMPRINT = [
    "#009E73",  # Brand green
    "#C475FD",  # Vermillion
    "#4467A3",  # Blue
    "#BD8233",  # Reddish purple
    "#AE3030",  # Orange
    "#2ABCCD",  # Sky blue
    "#954477",  # Yellow
]
colors = [IMPRINT[i % len(IMPRINT)] for i in range(n_dirs)]

# Create figure (square for polar plot)
p = figure(width=3600, height=3600, x_range=(-1.05, 1.05), y_range=(-1.05, 1.05), tools="", toolbar_location=None)

# Theme-adaptive styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Title styling
p.title = Title(text="polar-bar · bokeh · anyplot.ai", text_font_size="28pt", text_color=INK, align="center")

# Remove axes and grid for polar appearance
p.axis.visible = False
p.grid.visible = False

# Draw concentric reference circles
circle_radii = [0.25, 0.50, 0.75]
for r in circle_radii:
    p.circle(x=0, y=0, radius=r, fill_color=None, line_color=INK_SOFT, line_width=2, line_dash="dashed", line_alpha=0.3)

# Draw outer circle
p.circle(x=0, y=0, radius=0.85, fill_color=None, line_color=INK_SOFT, line_width=2, line_alpha=0.5)

# Draw radial lines for each direction
for i in range(n_dirs):
    angle = np.pi / 2 - angles[i]
    x_end = np.cos(angle) * 0.85
    y_end = np.sin(angle) * 0.85
    p.line([0, x_end], [0, y_end], line_color=INK_SOFT, line_width=1.5, line_alpha=0.3)

# Draw wedges (polar bars)
source = ColumnDataSource(
    data={
        "x": [0] * n_dirs,
        "y": [0] * n_dirs,
        "radius": radii.tolist(),
        "start_angle": start_angles.tolist(),
        "end_angle": end_angles.tolist(),
        "color": colors,
        "direction": directions,
        "frequency": frequencies.tolist(),
    }
)

p.wedge(
    x="x",
    y="y",
    radius="radius",
    start_angle="start_angle",
    end_angle="end_angle",
    fill_color="color",
    fill_alpha=0.85,
    line_color=INK_SOFT,
    line_width=3,
    source=source,
)

# Add direction labels around the plot
label_radius = 0.93
for i, direction in enumerate(directions):
    angle = np.pi / 2 - angles[i]
    x_label = np.cos(angle) * label_radius
    y_label = np.sin(angle) * label_radius

    label = Label(
        x=x_label,
        y=y_label,
        text=direction,
        text_font_size="22pt",
        text_color=INK,
        text_align="center",
        text_baseline="middle",
    )
    p.add_layout(label)

# Add frequency scale labels at reference circles
for r in circle_radii:
    freq_val = int(r / 0.75 * max_freq)
    label = Label(
        x=0.03,
        y=r + 0.015,
        text=f"{freq_val}",
        text_font_size="16pt",
        text_color=INK_SOFT,
        text_align="left",
        text_baseline="bottom",
    )
    p.add_layout(label)

# Save as HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 3600, 3600
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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
