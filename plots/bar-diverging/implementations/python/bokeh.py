""" anyplot.ai
bar-diverging: Diverging Bar Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-08
"""

import os
import sys
import time
from pathlib import Path


# Change to script directory for consistent file saving
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

# Remove current directory from sys.path to avoid shadowing bokeh package
sys.path = [p for p in sys.path if p != str(script_dir) and p != ""]
# Remove this file from sys.modules if it exists
if __name__ in sys.modules:
    del sys.modules[__name__]

from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, Span  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND_POS = "#009E73"  # Okabe-Ito position 1
BRAND_NEG = "#AE3030"  # imprint red — negative

# Data - Customer satisfaction survey responses (Net Promoter Score style)
categories = [
    "Product Quality",
    "Customer Service",
    "Delivery Speed",
    "Website Experience",
    "Price Value",
    "Return Policy",
    "Mobile App",
    "Warranty Service",
    "Tech Support",
    "Packaging",
]

# Net satisfaction scores: positive = more promoters, negative = more detractors
values = [45, 32, -15, 28, -8, 52, -22, 18, -35, 12]

# Sort by value for better pattern recognition
sorted_data = sorted(zip(categories, values, strict=True), key=lambda x: x[1])
categories_sorted = [item[0] for item in sorted_data]
values_sorted = [item[1] for item in sorted_data]

# Assign colors based on positive/negative values (Okabe-Ito palette)
colors = [BRAND_POS if v >= 0 else BRAND_NEG for v in values_sorted]

# Create ColumnDataSource
source = ColumnDataSource(data={"category": categories_sorted, "value": values_sorted, "color": colors})

# Create figure with horizontal bars (better for long category labels)
p = figure(
    width=4800,
    height=2700,
    y_range=categories_sorted,
    x_range=(-60, 70),
    title="bar-diverging · bokeh · anyplot.ai",
    x_axis_label="Net Satisfaction Score",
    y_axis_label="Category",
)

# Draw horizontal bars from 0
p.hbar(y="category", right="value", left=0, height=0.7, color="color", source=source, alpha=0.9)

# Add vertical line at zero baseline
zero_line = Span(location=0, dimension="height", line_color=INK_SOFT, line_width=2, line_dash="solid")
p.add_layout(zero_line)

# Style the plot
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

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
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid styling - subtle, 10% alpha
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.xgrid.grid_line_dash = "solid"
p.ygrid.grid_line_alpha = 0.0

# Legend styling (if present)
if p.legend:
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color = INK_SOFT
    p.legend.label_text_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome - Selenium 4 / Selenium Manager
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
