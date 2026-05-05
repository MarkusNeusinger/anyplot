""" anyplot.ai
swarm-basic: Basic Swarm Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-05
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

# Okabe-Ito palette — first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data — employee performance scores by department
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "HR"]
n_per_group = [45, 38, 52, 35]

categories = []
values = []

for dept, n in zip(departments, n_per_group, strict=False):
    categories.extend([dept] * n)
    if dept == "Engineering":
        scores = np.random.normal(82, 8, n)
    elif dept == "Marketing":
        scores = np.random.normal(75, 12, n)
    elif dept == "Sales":
        scores = np.concatenate([np.random.normal(65, 8, n // 2), np.random.normal(88, 6, n - n // 2)])
    else:  # HR
        scores = np.random.normal(78, 10, n)
        scores[0] = 45
        scores[1] = 98
    values.extend(np.clip(scores, 30, 100))

values = np.array(values)
categories = np.array(categories)

# Calculate swarm positions (jitter to avoid overlap)
x_jitter = np.zeros(len(values))
jitter_width = 0.35

for dept in departments:
    mask = categories == dept
    dept_values = values[mask]
    n_points = len(dept_values)

    sorted_indices = np.argsort(dept_values)
    sorted_values = dept_values[sorted_indices]

    jitter = np.zeros(n_points)
    bin_size = 3

    for j in range(n_points):
        nearby = np.abs(sorted_values - sorted_values[j]) < bin_size
        nearby_count = np.sum(nearby[:j])
        direction = 1 if nearby_count % 2 == 0 else -1
        offset = (nearby_count // 2 + 1) * 0.08
        jitter[j] = direction * min(offset, jitter_width)

    inverse_indices = np.argsort(sorted_indices)
    x_jitter[mask] = jitter[inverse_indices]

x_positions = np.array([departments.index(cat) + x_jitter[i] for i, cat in enumerate(categories)])

color_map = {dept: OKABE_ITO[i] for i, dept in enumerate(departments)}
colors = [color_map[cat] for cat in categories]

# Plot
source = ColumnDataSource(data={"x": x_positions, "y": values, "category": categories, "color": colors})

p = figure(
    width=4800,
    height=2700,
    title="swarm-basic · bokeh · anyplot.ai",
    x_axis_label="Department",
    y_axis_label="Performance Score",
    x_range=(-0.6, len(departments) - 0.4),
    y_range=(25, 108),
    tools="",
    toolbar_location=None,
)

p.scatter(x="x", y="y", source=source, size=18, color="color", alpha=0.75, line_color=PAGE_BG, line_width=1.5)

# Median markers for each category
for i, dept in enumerate(departments):
    mask = categories == dept
    median_val = np.median(values[mask])
    p.line(x=[i - 0.32, i + 0.32], y=[median_val, median_val], line_width=5, line_color=INK, line_alpha=0.65)

# X-axis category labels
p.xaxis.ticker = list(range(len(departments)))
p.xaxis.major_label_overrides = dict(enumerate(departments))

# Style — theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.title.text_font_size = "36pt"
p.title.align = "center"

p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "26pt"
p.yaxis.axis_label_text_font_size = "26pt"

p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.visible = False
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome (Selenium 4 / Selenium Manager)
# Window height is larger than figure height to account for browser chrome (~140px)
W, H = 4800, 2700
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H + 200}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H + 200)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
