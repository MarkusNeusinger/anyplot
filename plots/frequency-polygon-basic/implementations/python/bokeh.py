""" anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-17
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

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Three groups with different distributions
np.random.seed(42)

# Group A: Normal distribution centered at 65 (Morning Session)
group_a = np.random.normal(loc=65, scale=8, size=300)

# Group B: Normal distribution centered at 75, more spread (Afternoon Session)
group_b = np.random.normal(loc=75, scale=12, size=300)

# Group C: Slightly bimodal distribution (Evening Session)
group_c = np.concatenate([np.random.normal(loc=50, scale=6, size=150), np.random.normal(loc=60, scale=6, size=150)])

# Common bin edges for all groups
all_data = np.concatenate([group_a, group_b, group_c])
bins = np.linspace(all_data.min() - 5, all_data.max() + 5, 21)
bin_centers = (bins[:-1] + bins[1:]) / 2

# Compute histogram counts
counts_a, _ = np.histogram(group_a, bins=bins)
counts_b, _ = np.histogram(group_b, bins=bins)
counts_c, _ = np.histogram(group_c, bins=bins)

# Extend to zero at both ends for closed polygon shape
bin_width = bins[1] - bins[0]
x_extended = np.concatenate([[bin_centers[0] - bin_width], bin_centers, [bin_centers[-1] + bin_width]])
y_a_extended = np.concatenate([[0], counts_a, [0]])
y_b_extended = np.concatenate([[0], counts_b, [0]])
y_c_extended = np.concatenate([[0], counts_c, [0]])

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="frequency-polygon-basic · bokeh · anyplot.ai",
    x_axis_label="Test Score (points)",
    y_axis_label="Frequency (count)",
)

# Create sources
source_a = ColumnDataSource(data={"x": x_extended, "y": y_a_extended})
source_b = ColumnDataSource(data={"x": x_extended, "y": y_b_extended})
source_c = ColumnDataSource(data={"x": x_extended, "y": y_c_extended})

# Plot frequency polygons with fills
# Group A - Okabe-Ito 1 (Morning Session)
p.patch(x="x", y="y", source=source_a, fill_alpha=0.25, fill_color=IMPRINT[0], line_width=0)
p.line(x="x", y="y", source=source_a, line_color=IMPRINT[0], line_width=3, legend_label="Morning Session")
p.scatter(x=bin_centers, y=counts_a, size=15, color=IMPRINT[0], alpha=0.9)

# Group B - Okabe-Ito 2 (Afternoon Session)
p.patch(x="x", y="y", source=source_b, fill_alpha=0.25, fill_color=IMPRINT[1], line_width=0)
p.line(x="x", y="y", source=source_b, line_color=IMPRINT[1], line_width=3, legend_label="Afternoon Session")
p.scatter(x=bin_centers, y=counts_b, size=15, color=IMPRINT[1], alpha=0.9)

# Group C - Okabe-Ito 3 (Evening Session)
p.patch(x="x", y="y", source=source_c, fill_alpha=0.25, fill_color=IMPRINT[2], line_width=0)
p.line(x="x", y="y", source=source_c, line_color=IMPRINT[2], line_width=3, legend_label="Evening Session")
p.scatter(x=bin_centers, y=counts_c, size=15, color=IMPRINT[2], alpha=0.9)

# Theme-adaptive styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.title.text_font_size = "28pt"

p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"

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

# Legend styling
p.legend.location = "top_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "18pt"
p.legend.padding = 15
p.legend.spacing = 8
p.legend.glyph_height = 35
p.legend.glyph_width = 35
p.legend.margin = 20

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
