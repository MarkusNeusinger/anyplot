""" anyplot.ai
errorbar-basic: Basic Error Bar Plot
Library: bokeh 3.9.0 | Python 3.14.4
Quality: 84/100 | Updated: 2026-04-25
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, TeeHead, Whisker
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data — experimental measurements with associated uncertainties
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
means = np.array([25.3, 38.7, 42.1, 35.8, 48.2, 31.5])

# Asymmetric errors to demonstrate feature
lower_errors = np.array([2.1, 3.5, 2.8, 6.5, 4.8, 2.5])
upper_errors = np.array([2.1, 3.5, 2.8, 2.8, 2.2, 2.5])

upper = means + upper_errors
lower = means - lower_errors

source = ColumnDataSource(data={"categories": categories, "means": means, "upper": upper, "lower": lower})

# Plot
p = figure(
    width=4800,
    height=2700,
    x_range=categories,
    title="errorbar-basic · bokeh · anyplot.ai",
    x_axis_label="Experimental Group",
    y_axis_label="Response Value (units)",
    toolbar_location=None,
    tools="",
)

# Error bars (Whisker with TeeHead caps)
whisker = Whisker(
    base="categories",
    upper="upper",
    lower="lower",
    source=source,
    line_color=BRAND,
    line_width=5,
    upper_head=TeeHead(size=40, line_color=BRAND, line_width=5),
    lower_head=TeeHead(size=40, line_color=BRAND, line_width=5),
)
p.add_layout(whisker)

# Mean markers
p.scatter(x="categories", y="means", source=source, size=28, color=BRAND, line_color=PAGE_BG, line_width=2)

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_color = INK
p.title.text_font_size = "36pt"
p.title.text_font_style = "normal"
p.title.align = "left"

p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"

p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Subtle grid (y only)
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_color = None

p.y_range.start = 0
p.y_range.end = float(max(upper) * 1.15)

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html", title="errorbar-basic · bokeh · anyplot.ai")
save(p)
