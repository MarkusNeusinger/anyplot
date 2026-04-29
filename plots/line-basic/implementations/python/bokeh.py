""" anyplot.ai
line-basic: Basic Line Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-04-29
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Daily temperature readings for a month
np.random.seed(42)
days = np.arange(1, 32)
base_temp = 20 + 8 * np.sin(np.linspace(0, np.pi, 31))
temperature = base_temp + np.random.randn(31) * 2

source = ColumnDataSource(data={"day": days, "temperature": temperature})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="line-basic · bokeh · anyplot.ai",
    x_axis_label="Day of Month",
    y_axis_label="Temperature (°C)",
)

p.line(x="day", y="temperature", source=source, line_width=5, line_color=BRAND)
p.scatter(x="day", y="temperature", source=source, size=16, fill_color=BRAND, line_color=PAGE_BG, line_width=3)

# Style — text sizes for 4800×2700 px
p.title.text_font_size = "42pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "32pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "24pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_color = INK_SOFT

# Background and borders
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Axis lines and ticks
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2

# Grid — y-axis only, subtle
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

p.toolbar_location = None

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)
