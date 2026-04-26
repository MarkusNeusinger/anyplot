"""anyplot.ai
lollipop-basic: Basic Lollipop Chart
Library: bokeh | Python 3.13
Quality: pending | Updated: 2026-04-26
"""

import os

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, NumeralTickFormatter
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data — product sales by category (pre-sorted descending)
categories = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports",
    "Books",
    "Toys",
    "Food",
    "Beauty",
    "Automotive",
    "Office",
]
values = [85000, 72000, 61000, 53000, 47000, 39000, 33000, 28000, 22000, 15000]

source = ColumnDataSource(data={"categories": categories, "values": values, "zeros": [0] * len(values)})

# Plot
p = figure(
    width=4800,
    height=2700,
    x_range=categories,
    title="lollipop-basic · bokeh · anyplot.ai",
    x_axis_label="Product Category",
    y_axis_label="Sales (USD)",
    toolbar_location=None,
)

p.segment(x0="categories", y0="zeros", x1="categories", y1="values", source=source, line_width=4, color=BRAND)

p.scatter(x="categories", y="values", source=source, size=42, color=BRAND, line_color=PAGE_BG, line_width=3)

# Style
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.title.text_font_style = "normal"

p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

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

p.xaxis.major_label_orientation = 0.6

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.yaxis.formatter = NumeralTickFormatter(format="$0,0")

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)
