""" anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-15
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data
iris = load_iris()
X = iris.data
y = iris.target
species_names = ["Setosa", "Versicolor", "Virginica"]

# Normalize variables to similar scales
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Generate t values from -π to π
t_values = np.linspace(-np.pi, np.pi, 200)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="andrews-curves · bokeh · anyplot.ai",
    x_axis_label="t (radians)",
    y_axis_label="f(t)",
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
)

# Style text
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_color = INK_SOFT

# Style axes and grid
p.outline_line_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Store legend items
legend_items = []

# Plot curves for each species using vectorized Andrews curves
for species_idx in range(3):
    species_mask = y == species_idx
    X_species = X_scaled[species_mask]

    first_line = None

    for coeffs in X_species:
        # Vectorized Andrews curve: f(t) = x1/sqrt(2) + x2*sin(t) + x3*cos(t) + x4*sin(2t) + ...
        n = len(coeffs)
        curve_values = coeffs[0] / np.sqrt(2)
        for i in range(1, n):
            if i % 2 == 1:
                curve_values += coeffs[i] * np.sin((i // 2 + 1) * t_values)
            else:
                curve_values += coeffs[i] * np.cos((i // 2) * t_values)

        source = ColumnDataSource(
            data={"x": t_values, "y": curve_values, "species": [species_names[species_idx]] * len(t_values)}
        )

        line = p.line(x="x", y="y", source=source, line_color=IMPRINT[species_idx], line_alpha=0.4, line_width=3)

        if first_line is None:
            first_line = line

    legend_items.append((species_names[species_idx], [first_line]))

# Add hover tool
hover = HoverTool(tooltips=[("t", "@x{0.00}"), ("f(t)", "@y{0.00}"), ("Species", "@species")])
p.add_tools(hover)

# Create and add legend
legend = Legend(items=legend_items, location="top_right")
legend.label_text_font_size = "18pt"
legend.label_text_color = INK_SOFT
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.95
legend.border_line_color = INK_SOFT
p.add_layout(legend, "right")

# Save HTML
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
