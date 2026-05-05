"""anyplot.ai
waffle-basic: Basic Waffle Chart
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-05-05
"""

import os
import time
from pathlib import Path

from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always brand green)
PALETTE = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Survey results on renewable energy adoption
categories = ["Solar", "Wind", "Hydro", "Geothermal"]
values = [48, 25, 18, 9]  # Percentages summing to 100

# Build waffle grid (10x10 = 100 squares)
grid_size = 10
total_squares = grid_size * grid_size

# Assign category to each square based on percentages
square_categories = []
color_map = []
for i, (cat, val) in enumerate(zip(categories, values, strict=True)):
    square_categories.extend([cat] * val)
    color_map.extend([PALETTE[i]] * val)

# Create grid coordinates (fill left-to-right, bottom-to-top)
x_coords = []
y_coords = []
for idx in range(total_squares):
    x_coords.append(idx % grid_size)
    y_coords.append(idx // grid_size)

source = ColumnDataSource(data={"x": x_coords, "y": y_coords, "category": square_categories, "color": color_map})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="Renewable Energy Sources · waffle-basic · bokeh · anyplot.ai",
    x_range=(-0.7, grid_size - 0.3),
    y_range=(-0.7, grid_size - 0.3),
    tools="",
    toolbar_location=None,
)

# Draw squares with small gap between them
square_size = 0.88
renderers = []
for i, (cat, color) in enumerate(zip(categories, PALETTE, strict=True)):
    # Filter data for this category
    indices = [j for j, c in enumerate(square_categories) if c == cat]
    cat_source = ColumnDataSource(
        data={
            "x": [x_coords[j] for j in indices],
            "y": [y_coords[j] for j in indices],
            "category": [cat] * len(indices),
            "percentage": [values[i]] * len(indices),
        }
    )
    r = p.rect(
        x="x",
        y="y",
        width=square_size,
        height=square_size,
        source=cat_source,
        fill_color=color,
        line_color=PAGE_BG,
        line_width=2.5,
        fill_alpha=1.0,
    )
    renderers.append((f"{cat} ({values[i]}%)", [r]))

# Add hover tool
hover = HoverTool(tooltips=[("Category", "@category"), ("Percentage", "@percentage%")])
p.add_tools(hover)

# Add legend
legend = Legend(items=[LegendItem(label=label, renderers=rends) for label, rends in renderers])
legend.label_text_font_size = "18pt"
legend.glyph_height = 35
legend.glyph_width = 35
legend.spacing = 12
legend.padding = 15
legend.location = "top_right"
legend.background_fill_color = ELEVATED_BG
legend.border_line_color = INK_SOFT
legend.label_text_color = INK_SOFT
p.add_layout(legend, "right")

# Style the plot
p.title.text_font_size = "28pt"
p.title.align = "center"
p.title.text_color = INK

# Hide axes
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Set background
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
