""" anyplot.ai
contour-basic: Basic Contour Plot
Library: bokeh 3.9.0 | Python 3.14.4
Quality: 90/100 | Updated: 2026-04-24
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.palettes import Viridis256
from bokeh.plotting import figure


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data — simulated topographic elevation map of a 10km x 10km mountain region
x = np.linspace(0, 10, 90)
y = np.linspace(0, 10, 90)
X, Y = np.meshgrid(x, y)

elevation = (
    850 * np.exp(-((X - 7) ** 2 + (Y - 7) ** 2) / 4.0)
    + 550 * np.exp(-((X - 2.5) ** 2 + (Y - 3) ** 2) / 3.0)
    - 180 * np.exp(-((X - 5) ** 2 + (Y - 5) ** 2) / 8.0)
    + 12 * X
    + 350
)

levels = np.linspace(elevation.min(), elevation.max(), 14)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="Mountain Terrain · contour-basic · bokeh · anyplot.ai",
    x_axis_label="Distance East (km)",
    y_axis_label="Distance North (km)",
    toolbar_location=None,
    x_range=(0, 10),
    y_range=(0, 10),
    match_aspect=True,
)

contour = p.contour(
    x=X, y=Y, z=elevation, levels=levels, fill_color=Viridis256, line_color=PAGE_BG, line_width=2, line_alpha=0.45
)

colorbar = contour.construct_color_bar(
    title="Elevation (m)",
    title_text_font_size="26pt",
    title_text_color=INK,
    title_text_font_style="normal",
    title_standoff=20,
    major_label_text_font_size="22pt",
    major_label_text_color=INK_SOFT,
    background_fill_color=PAGE_BG,
    border_line_color=None,
    width=60,
    padding=20,
)
p.add_layout(colorbar, "right")

# Typography — sized for 4800×2700 canvas
p.title.text_font_size = "42pt"
p.title.text_font_style = "bold"
p.title.text_color = INK
p.title.align = "center"

p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"
p.xaxis.axis_label_standoff = 28
p.yaxis.axis_label_standoff = 28

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.min_border_right = 60

p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Filled contour covers the plot area, so disable grid to avoid noise
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

p.xaxis.ticker.desired_num_ticks = 10
p.yaxis.ticker.desired_num_ticks = 8

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html", title="contour-basic · bokeh · anyplot.ai")
save(p)
