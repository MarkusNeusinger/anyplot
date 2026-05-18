"""anyplot.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 60/100 | Updated: 2026-05-18
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, FactorRange, HoverTool
from bokeh.plotting import figure
from bokeh.resources import CDN
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive colors
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data color (brand green, theme-independent)
DATA_COLOR = "#009E73"

# Data - Reaction times (ms) across 4 experimental conditions
np.random.seed(42)

categories = ["Control", "Low Dose", "Medium Dose", "High Dose"]
n_per_group = 50

# Generate different distributions for each condition
data = {
    "Control": np.random.normal(350, 50, n_per_group),
    "Low Dose": np.random.normal(320, 45, n_per_group),
    "Medium Dose": np.random.normal(280, 60, n_per_group),
    "High Dose": np.random.normal(250, 40, n_per_group),
}

# Create figure with padding for violins
p = figure(
    width=4800,
    height=2700,
    title="violin-swarm · Python · bokeh · anyplot.ai",
    x_range=FactorRange(*categories, range_padding=0.15),
    y_axis_label="Reaction Time (ms)",
    x_axis_label="Experimental Condition",
)

# Background and chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Styling - larger text for 4800x2700 canvas
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
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Build violin shapes and swarm points
violin_patches_x = []
violin_patches_y = []
swarm_x = []
swarm_y = []
swarm_categories = []

for i, cat in enumerate(categories):
    values = data[cat]

    # Kernel density estimation for violin
    kde = stats.gaussian_kde(values)
    y_range = np.linspace(values.min() - 20, values.max() + 20, 200)
    density = kde(y_range)

    # Normalize density to max width of 0.4 (so violin fits within category space)
    max_width = 0.35
    density_normalized = density / density.max() * max_width

    # Create violin shape (mirrored density)
    x_violin = np.concatenate([i - density_normalized, (i + density_normalized)[::-1]])
    y_violin = np.concatenate([y_range, y_range[::-1]])

    violin_patches_x.append(x_violin.tolist())
    violin_patches_y.append(y_violin.tolist())

    # Create swarm points (jitter within violin boundary)
    for val in values:
        # Get the density at this y value to determine jitter range
        val_density = kde(val)[0]
        jitter_range = (val_density / density.max()) * max_width * 0.8
        jitter = np.random.uniform(-jitter_range, jitter_range)
        swarm_x.append(i + jitter)
        swarm_y.append(val)
        swarm_categories.append(cat)

# Draw violins as patches (semi-transparent)
for vx, vy in zip(violin_patches_x, violin_patches_y, strict=True):
    p.patch(vx, vy, fill_color=DATA_COLOR, fill_alpha=0.4, line_color=DATA_COLOR, line_width=2)

# Draw swarm points with HoverTool
swarm_source = ColumnDataSource(data={"x": swarm_x, "y": swarm_y, "category": swarm_categories})
hover = HoverTool(tooltips=[("Category", "@category"), ("Value (ms)", "@y{0.0}")])
p.add_tools(hover)
p.scatter("x", "y", source=swarm_source, size=12, color=DATA_COLOR, alpha=0.7, line_color=INK_SOFT, line_width=1)

# Save HTML
output_file(f"plot-{THEME}.html")
save(p, resources=CDN)

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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
