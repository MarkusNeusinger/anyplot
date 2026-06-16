""" anyplot.ai
histogram-density: Density Histogram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-11
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series for histogram, second for PDF)
COLOR_HIST = "#009E73"
COLOR_PDF = "#C475FD"

# Data - Test scores with normal-like distribution
np.random.seed(42)
mu, sigma = 75, 12
scores = np.random.normal(loc=mu, scale=sigma, size=500)

# Calculate histogram with density normalization
bin_edges = np.linspace(scores.min() - 5, scores.max() + 5, 31)
hist_counts, edges = np.histogram(scores, bins=bin_edges, density=True)
left_edges = edges[:-1]
right_edges = edges[1:]

# Theoretical normal PDF for overlay
x_pdf = np.linspace(scores.min() - 10, scores.max() + 10, 200)
pdf_values = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_pdf - mu) / sigma) ** 2)

# Sources
hist_source = ColumnDataSource(
    data={"left": left_edges, "right": right_edges, "top": hist_counts, "bottom": [0] * len(hist_counts)}
)
pdf_source = ColumnDataSource(data={"x": x_pdf, "y": pdf_values})

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="histogram-density · bokeh · anyplot.ai",
    x_axis_label="Test Score",
    y_axis_label="Density (Probability per Unit)",
)

# Plot histogram bars
p.quad(
    left="left",
    right="right",
    top="top",
    bottom="bottom",
    source=hist_source,
    fill_color=COLOR_HIST,
    fill_alpha=0.7,
    line_color=PAGE_BG,
    line_width=2,
    legend_label="Empirical Distribution",
)

# Plot theoretical PDF overlay
p.line(x="x", y="y", source=pdf_source, line_color=COLOR_PDF, line_width=5, legend_label="Normal PDF (μ=75, σ=12)")

# Styling for 4800x2700 px
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Theme-adaptive colors
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.title.text_color = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT

# Subtle grid
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Legend styling
p.legend.label_text_font_size = "20pt"
p.legend.label_text_color = INK_SOFT
p.legend.location = "top_left"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT

# Y-axis starts at zero
p.y_range.start = 0

# Save interactive HTML
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
