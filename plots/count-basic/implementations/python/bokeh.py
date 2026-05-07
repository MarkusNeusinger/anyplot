""" anyplot.ai
count-basic: Basic Count Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-07
"""

import os
import sys
import time
from pathlib import Path


sys.path = [p for p in sys.path if "implementations" not in p]  # noqa: E402

import numpy as np  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, LabelSet  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Survey responses simulating a customer satisfaction survey
np.random.seed(42)
responses = np.random.choice(
    ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"],
    size=200,
    p=[0.25, 0.35, 0.20, 0.12, 0.08],
)

# Count occurrences
categories, counts = np.unique(responses, return_counts=True)
# Sort by count descending for better readability
sorted_indices = np.argsort(-counts)
categories = categories[sorted_indices]
counts = counts[sorted_indices]

# Create data source
source = ColumnDataSource(
    data={"category": categories.tolist(), "count": counts.tolist(), "label": [str(c) for c in counts]}
)

# Create figure with categorical x-axis
p = figure(
    x_range=categories.tolist(),
    width=4800,
    height=2700,
    title="count-basic · bokeh · anyplot.ai",
    x_axis_label="Response Category",
    y_axis_label="Number of Responses",
    toolbar_location=None,
)

# Plot bars with Okabe-Ito green
p.vbar(x="category", top="count", source=source, width=0.7, color=BRAND, alpha=0.85, line_color=INK_SOFT, line_width=2)

# Add count labels above bars
labels = LabelSet(
    x="category",
    y="count",
    text="label",
    source=source,
    text_align="center",
    text_baseline="bottom",
    y_offset=10,
    text_font_size="22pt",
    text_color=INK_SOFT,
)
p.add_layout(labels)

# Style the plot
p.title.text_font_size = "28pt"
p.title.align = "center"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Axis and background
p.xaxis.major_label_orientation = 0.4
p.y_range.start = 0
p.y_range.end = max(counts) * 1.15
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save files in script directory
script_dir = Path(__file__).parent
html_path = script_dir / f"plot-{THEME}.html"
png_path = script_dir / f"plot-{THEME}.png"

output_file(str(html_path))
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
driver.get(f"file://{html_path.resolve()}")
time.sleep(3)
driver.save_screenshot(str(png_path))
driver.quit()
