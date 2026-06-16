""" anyplot.ai
histogram-kde: Histogram with KDE Overlay
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-06
"""

import os
import sys
import time
from pathlib import Path

import numpy as np


# Remove current directory from path to avoid importing bokeh.py instead of bokeh package
script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if sys.path and sys.path[0] in ("", ".", script_dir):
    sys.path.pop(0)

# Change to script directory to save output files there
os.chdir(script_dir)

from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, HoverTool  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme setup
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
HISTOGRAM_COLOR = "#009E73"  # Brand green
KDE_COLOR = "#C475FD"  # Vermillion

# Data - Simulating stock returns distribution (realistic financial data)
np.random.seed(42)
# Mix of normal market conditions and some fat-tail events
main_returns = np.random.normal(0.05, 2.5, 800)  # Daily returns in %
tail_events = np.concatenate(
    [
        np.random.normal(-8, 1.5, 50),  # Negative tail events
        np.random.normal(10, 2, 50),  # Positive tail events
    ]
)
values = np.concatenate([main_returns, tail_events])

# Histogram computation (density-normalized)
bin_count = 40
hist, bin_edges = np.histogram(values, bins=bin_count, density=True)

# KDE computation using Gaussian kernel (Scott's rule bandwidth)
x_kde = np.linspace(values.min() - 2, values.max() + 2, 500)
bandwidth = 1.06 * np.std(values) * len(values) ** (-1 / 5)
y_kde = np.zeros_like(x_kde)
for xi in values:
    y_kde += np.exp(-0.5 * ((x_kde - xi) / bandwidth) ** 2)
y_kde /= len(values) * bandwidth * np.sqrt(2 * np.pi)

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="histogram-kde · bokeh · anyplot.ai",
    x_axis_label="Daily Return (%)",
    y_axis_label="Density",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Histogram using quad glyphs
hist_source = ColumnDataSource(
    data={"left": bin_edges[:-1], "right": bin_edges[1:], "top": hist, "bottom": [0] * len(hist)}
)

p.quad(
    left="left",
    right="right",
    top="top",
    bottom="bottom",
    source=hist_source,
    fill_color=HISTOGRAM_COLOR,
    fill_alpha=0.5,
    line_color=HISTOGRAM_COLOR,
    line_alpha=0.8,
    line_width=2,
    legend_label="Histogram",
)

# Add hover tool for histogram
hist_hover = HoverTool(tooltips=[("Range", "@left{0.00} - @right{0.00}"), ("Density", "@top{0.00}")])
p.add_tools(hist_hover)

# KDE curve
kde_source = ColumnDataSource(data={"x": x_kde, "y": y_kde})
p.line(x="x", y="y", source=kde_source, line_color=KDE_COLOR, line_width=5, legend_label="KDE")

# Add hover tool for KDE curve
kde_hover = HoverTool(tooltips=[("Return (%)", "@x{0.00}"), ("Density", "@y{0.0000}")])
p.add_tools(kde_hover)

# Title styling
p.title.text_font_size = "28pt"
p.title.text_color = INK

# Axis styling
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Grid styling - subtle
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Legend styling
p.legend.label_text_font_size = "20pt"
p.legend.location = "top_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# Axis and border colors
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Save as HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
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
