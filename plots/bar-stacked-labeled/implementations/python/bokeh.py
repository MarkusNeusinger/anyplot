""" anyplot.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Quarterly revenue by product category
np.random.seed(42)
categories = ["Q1", "Q2", "Q3", "Q4"]
components = ["Electronics", "Clothing", "Home & Garden", "Sports"]

data = {
    "Electronics": [45, 52, 48, 68],
    "Clothing": [32, 38, 55, 72],
    "Home & Garden": [28, 42, 38, 35],
    "Sports": [18, 25, 32, 45],
}

# Calculate totals for labels
totals = [sum(data[comp][i] for comp in components) for i in range(len(categories))]

# Create figure with categorical x-axis
p = figure(
    x_range=categories,
    width=4800,
    height=2700,
    title="bar-stacked-labeled · Python · bokeh · anyplot.ai",
    x_axis_label="Quarter",
    y_axis_label="Revenue ($M)",
    toolbar_location="right",
)

# Track bottom positions for stacking
bottoms = [0] * len(categories)

# Plot stacked bars
for _comp_idx, (comp, color) in enumerate(zip(components, IMPRINT, strict=True)):
    tops = [b + v for b, v in zip(bottoms, data[comp], strict=True)]
    source = ColumnDataSource(
        data={
            "categories": categories,
            "values": data[comp],
            "bottoms": bottoms.copy(),
            "tops": tops,
            "component": [comp] * len(categories),
        }
    )

    bars = p.vbar(
        x="categories",
        top="tops",
        bottom="bottoms",
        width=0.7,
        source=source,
        color=color,
        legend_label=comp,
        line_color="white",
        line_width=2,
    )

    # Add hover tool to show detailed segment information
    hover = HoverTool(
        renderers=[bars], tooltips=[("Quarter", "@categories"), ("Category", "@component"), ("Value", "@values M")]
    )
    p.add_tools(hover)

    # Update bottoms for next stack
    bottoms = tops.copy()

# Add total labels above each bar stack
label_source = ColumnDataSource(
    data={
        "x": categories,
        "y": [t + 5 for t in totals],  # Offset above bars
        "text": [f"${t}M" for t in totals],
    }
)

labels = LabelSet(
    x="x",
    y="y",
    text="text",
    source=label_source,
    text_font_size="36pt",
    text_font_style="bold",
    text_color=INK,
    text_align="center",
    text_baseline="bottom",
)
p.add_layout(labels)

# Styling for large canvas (4800x2700)
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Axis line styling
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Legend styling - position in bottom left to avoid crowding labels
p.legend.location = "bottom_left"
p.legend.label_text_font_size = "18pt"
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 35
p.legend.glyph_width = 35
p.legend.spacing = 12
p.legend.padding = 20
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.border_line_color = INK_SOFT

# Background colors (theme-adaptive)
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Set y-axis range to accommodate labels
p.y_range.end = max(totals) + 30

# Save HTML (required for interactive library)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome (Selenium)
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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
