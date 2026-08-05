"""anyplot.ai
bar-horizontal: Horizontal Bar Chart
Library: bokeh 3.9.2 | Python 3.13.13
Quality: 88/100 | Updated: 2026-08-05
"""

import os
import sys
import time
from pathlib import Path


if sys.path and sys.path[0] in ("", "."):
    sys.path.pop(0)

from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, LabelSet, PrintfTickFormatter
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Top Programming Languages by Developer Popularity (%)
categories = ["JavaScript", "Python", "TypeScript", "Java", "C#", "C++", "PHP", "Go", "Rust", "Kotlin"]
values = [65.6, 49.3, 38.5, 33.3, 28.7, 22.4, 18.2, 14.3, 13.1, 9.2]

# Sort by value (smallest to largest for bottom-to-top display)
sorted_data = sorted(zip(categories, values, strict=True), key=lambda x: x[1])
categories_sorted = [x[0] for x in sorted_data]
values_sorted = [x[1] for x in sorted_data]
labels_sorted = [f"{v:.1f}%" for v in values_sorted]

# Create data source (bars + end-of-bar value labels share one source)
source = ColumnDataSource(data={"categories": categories_sorted, "values": values_sorted, "labels": labels_sorted})

# Create figure with categorical y-axis (3200 x 1800 px, the canonical landscape canvas)
p = figure(
    width=3200,
    height=1800,
    y_range=categories_sorted,
    x_axis_label="Developer Popularity (%)",
    title="bar-horizontal · python · bokeh · anyplot.ai",
    toolbar_location=None,  # bokeh's default toolbar adds ~30-50px above the plot,
    # which would shrink the saved screenshot below the 3200x1800 target.
    min_border_bottom=160,  # room for 34pt x-tick labels + 42pt x-axis label
    min_border_left=320,  # room for 34pt category tick labels (up to "TypeScript")
    min_border_top=110,  # room for 50pt title
    min_border_right=80,  # room for value labels near the right edge
)

# Draw horizontal bars with Okabe-Ito color #009E73
p.hbar(
    y="categories", right="values", height=0.7, source=source, color="#009E73", line_color=INK, line_width=2, alpha=0.9
)

# End-of-bar value labels for direct, at-a-glance reading of each value
value_labels = LabelSet(
    x="values",
    y="categories",
    text="labels",
    source=source,
    x_offset=12,
    text_font_size="26pt",
    text_color=INK_SOFT,
    text_baseline="middle",
)
p.add_layout(value_labels)

# Style title
p.title.text_font_size = "50pt"
p.title.align = "center"
p.title.text_color = INK

# Style axes for the 3200x1800 canvas
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_standoff = 20
p.yaxis.axis_label_standoff = 20
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.formatter = PrintfTickFormatter(format="%d%%")

# Configure grid
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.12
p.ygrid.grid_line_alpha = 0

# Theme-adaptive background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Set x-axis range starting from 0, with headroom for the end-of-bar labels
p.x_range.start = 0
p.x_range.end = 78

# Save as HTML for interactivity
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 3200, 1800
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
# Headless Chrome's --window-size sets the OUTER window, which still reserves a
# phantom title-bar height even headless — pin the viewport exactly via CDP so
# the screenshot lands at exactly W x H instead of coming out short.
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
