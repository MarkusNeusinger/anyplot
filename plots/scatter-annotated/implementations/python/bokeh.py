"""anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: bokeh | Python 3.13
Quality: pending | Created: 2025-12-30
"""

import sys


sys.path = [p for p in sys.path if not p.endswith("implementations/python")]

import os  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import bokeh.io  # noqa: E402
import bokeh.models  # noqa: E402
import bokeh.plotting  # noqa: E402
import numpy as np  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Create aliases to avoid name shadowing with bokeh.py module name
output_file = bokeh.io.output_file
save = bokeh.io.save
ColumnDataSource = bokeh.models.ColumnDataSource
LabelSet = bokeh.models.LabelSet
figure = bokeh.plotting.figure

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Company market performance example
np.random.seed(42)
companies = [
    "TechCorp",
    "DataSys",
    "CloudNet",
    "AIVenture",
    "NetFlow",
    "CodeBase",
    "ByteWorks",
    "DigiCore",
    "InfoTech",
    "WebScale",
    "AppLogic",
    "SoftPeak",
    "CyberLink",
    "DevOps",
    "QuantumBit",
]

# Revenue (billions) and Market Cap (billions)
revenue = np.array([12.5, 8.3, 22.1, 5.7, 15.8, 9.2, 18.4, 6.9, 11.3, 25.6, 7.4, 14.2, 19.8, 4.5, 10.1])
market_cap = np.array([45.2, 28.1, 85.3, 32.5, 52.8, 35.6, 68.9, 25.4, 41.7, 98.2, 22.3, 55.4, 72.1, 18.9, 38.5])

# Create ColumnDataSource with label offsets
source = ColumnDataSource(
    data={
        "x": revenue,
        "y": market_cap,
        "labels": companies,
        "x_offset": np.full(len(companies), 0.8),
        "y_offset": np.full(len(companies), 2.0),
    }
)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="scatter-annotated · bokeh · anyplot.ai",
    x_axis_label="Revenue (Billions $)",
    y_axis_label="Market Cap (Billions $)",
    tools="pan,wheel_zoom,box_zoom,reset",
)

# Plot scatter points
p.scatter(x="x", y="y", source=source, size=40, color=BRAND, alpha=0.7, line_color=PAGE_BG, line_width=2)

# Add connecting line segments from points to labels
segments_source = ColumnDataSource(data={"x0": revenue, "y0": market_cap, "x1": revenue + 0.8, "y1": market_cap + 2.0})
p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=segments_source, line_color=INK_SOFT, line_width=1, line_alpha=0.4)

# Add text labels
labels = LabelSet(
    x="x",
    y="y",
    text="labels",
    source=source,
    x_offset=30,
    y_offset=45,
    text_font_size="24pt",
    text_color=INK,
    text_font_style="normal",
)
p.add_layout(labels)

# Style title
p.title.text_font_size = "28pt"
p.title.text_color = INK

# Style axes labels
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

# Style tick labels
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Style grid
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Axis styling
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 4800, 2700
opts = Options()
opts.binary_location = "/usr/bin/chromium"
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
