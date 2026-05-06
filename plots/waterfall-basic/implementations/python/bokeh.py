"""anyplot.ai
waterfall-basic: Basic Waterfall Chart
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-05-06
"""

import os
import time
from pathlib import Path

from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, FactorRange, HoverTool, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
POSITIVE = "#009E73"  # brand green for positive changes
NEGATIVE = "#D55E00"  # vermillion for negative changes
TOTAL = "#0072B2"  # blue for totals

# Data - quarterly financial breakdown
categories = ["Starting Revenue", "Product Sales", "Services", "Refunds", "Operating Costs", "Marketing", "Net Income"]
changes = [150000, 50000, 35000, -8000, -75000, -22000, 0]

# Calculate waterfall positions
running_total = 0
bar_bottoms = []
bar_tops = []
bar_colors = []
display_values = []

for i, (_cat, change) in enumerate(zip(categories, changes, strict=True)):
    if i == 0:
        # Starting total - full bar from 0
        running_total = change
        bar_bottoms.append(0)
        bar_tops.append(running_total)
        bar_colors.append(TOTAL)
        display_values.append(running_total)
    elif i == len(categories) - 1:
        # Final total - full bar from 0 to current running total
        bar_bottoms.append(0)
        bar_tops.append(running_total)
        bar_colors.append(TOTAL)
        display_values.append(running_total)
    else:
        # Intermediate changes
        if change >= 0:
            bar_bottoms.append(running_total)
            bar_tops.append(running_total + change)
            bar_colors.append(POSITIVE)
        else:
            bar_bottoms.append(running_total + change)
            bar_tops.append(running_total)
            bar_colors.append(NEGATIVE)
        running_total += change
        display_values.append(change)

# Create data source
source = ColumnDataSource(
    data={
        "categories": categories,
        "bottom": bar_bottoms,
        "top": bar_tops,
        "color": bar_colors,
        "display": [f"${v:,.0f}" for v in display_values],
    }
)

# Create figure
p = figure(
    x_range=FactorRange(*categories, range_padding=0.1),
    width=4800,
    height=2700,
    title="waterfall-basic · bokeh · anyplot.ai",
    x_axis_label="Financial Category",
    y_axis_label="Amount ($)",
    toolbar_location=None,
)

# Draw bars
p.vbar(
    x="categories",
    top="top",
    bottom="bottom",
    width=0.6,
    source=source,
    color="color",
    line_color=INK_SOFT,
    line_width=2,
    alpha=0.9,
)

# Add HoverTool for interactivity
hover = HoverTool(tooltips=[("Category", "@categories"), ("Amount", "@display")])
p.add_tools(hover)

# Calculate running totals for connector lines
running_totals = []
rt = 0
for i, change in enumerate(changes):
    if i == 0:
        rt = change
    elif i < len(changes) - 1:
        rt += change
    running_totals.append(rt)

# Draw connector lines between bars
for i in range(len(categories) - 2):
    connector_y = running_totals[i]
    p.line(
        x=[categories[i], categories[i + 1]],
        y=[connector_y, connector_y],
        line_color=INK_SOFT,
        line_width=2,
        line_dash="dashed",
        alpha=0.5,
    )

# Add value labels on bars
max_value = max(bar_tops)
label_offset = max_value * 0.03

for i, (_cat, _bottom, top, display_val) in enumerate(
    zip(categories, bar_bottoms, bar_tops, display_values, strict=True)
):
    label_y = top + label_offset

    if i == 0 or i == len(categories) - 1:
        label_text = f"${display_val:,.0f}"
    else:
        if display_val >= 0:
            label_text = f"+${display_val:,.0f}"
        else:
            label_text = f"-${abs(display_val):,.0f}"

    label = Label(
        x=i,
        y=label_y,
        text=label_text,
        text_font_size="20pt",
        text_align="center",
        text_baseline="bottom",
        text_color=INK,
    )
    p.add_layout(label)

# Style
p.title.text_font_size = "28pt"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_orientation = 0.3

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.1

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.y_range.start = 0
p.y_range.end = max_value * 1.15
p.min_border_left = 80

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with Selenium
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
