""" anyplot.ai
pyramid-basic: Basic Pyramid Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-04-29
"""

import os

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, CustomJSTickFormatter, HoverTool, Range1d, Span
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

MALE_COLOR = "#009E73"  # Okabe-Ito position 1
FEMALE_COLOR = "#D55E00"  # Okabe-Ito position 2

# Data - Population by age group (in thousands)
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
male_population = [45, 52, 68, 82, 75, 65, 48, 32, 15]
female_population = [43, 50, 72, 85, 78, 70, 55, 40, 22]
male_negative = [-v for v in male_population]

source_male = ColumnDataSource(data={"age": age_groups, "population": male_negative, "value": male_population})
source_female = ColumnDataSource(data={"age": age_groups, "population": female_population, "value": female_population})

# Plot
p = figure(
    width=4800,
    height=2700,
    y_range=age_groups,
    x_range=Range1d(-100, 100),
    title="pyramid-basic · bokeh · anyplot.ai",
    x_axis_label="Population (thousands)",
    y_axis_label="Age Group",
)

bar_height = 0.7
male_bars = p.hbar(
    y="age",
    right="population",
    height=bar_height,
    source=source_male,
    color=MALE_COLOR,
    alpha=0.85,
    legend_label="Male",
)
female_bars = p.hbar(
    y="age",
    right="population",
    height=bar_height,
    source=source_female,
    color=FEMALE_COLOR,
    alpha=0.85,
    legend_label="Female",
)

# HoverTools for interactivity
p.add_tools(HoverTool(renderers=[male_bars], tooltips=[("Age Group", "@age"), ("Male", "@value{0,0} thousand")]))
p.add_tools(HoverTool(renderers=[female_bars], tooltips=[("Age Group", "@age"), ("Female", "@value{0,0} thousand")]))

# Center line at x=0 via Span — adapts to full plot height automatically
center_line = Span(location=0, dimension="height", line_color=INK_SOFT, line_width=2, line_alpha=0.5)
p.add_layout(center_line)

# Show absolute values on x-axis (both sides positive)
p.xaxis.formatter = CustomJSTickFormatter(code="return Math.abs(tick).toString()")

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

p.legend.location = "bottom_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "18pt"
p.legend.background_fill_alpha = 0.9

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)
