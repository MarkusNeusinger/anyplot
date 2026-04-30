"""anyplot.ai
step-basic: Basic Step Plot
Library: bokeh | Python 3.13
Quality: pending | Updated: 2026-04-30
"""

import os

from bokeh.io import export_png, output_file
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, save


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Monthly cumulative sales showing discrete jumps
months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
cumulative_sales = [15, 28, 42, 55, 71, 89, 102, 118, 135, 156, 172, 195]

source = ColumnDataSource(data={"month": months, "sales": cumulative_sales})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="step-basic · bokeh · anyplot.ai",
    x_axis_label="Month",
    y_axis_label="Cumulative Sales (units)",
    tools="",
    toolbar_location=None,
)

# Step line (after/post mode - value holds until next change occurs)
p.step(x="month", y="sales", source=source, line_width=5, color=BRAND, mode="after")

# Markers at data points to highlight where changes occur
p.scatter(x="month", y="sales", source=source, size=18, color=BRAND, line_color=PAGE_BG, line_width=3)

# Style - text sizes for 4800x2700 px canvas
p.title.text_font_size = "28pt"
p.title.text_font_style = "bold"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Chrome - axes and ticks
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid - subtle solid lines
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)
