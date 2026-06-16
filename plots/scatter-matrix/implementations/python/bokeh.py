""" anyplot.ai
scatter-matrix: Scatter Plot Matrix
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-09
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, Title
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]
species_list = ["setosa", "versicolor", "virginica"]

# Data - Iris-like dataset with 4 variables and species groups
np.random.seed(42)

species = np.repeat(species_list, 50)

sepal_length = np.concatenate(
    [np.random.normal(5.0, 0.35, 50), np.random.normal(5.9, 0.52, 50), np.random.normal(6.6, 0.64, 50)]
)

sepal_width = np.concatenate(
    [np.random.normal(3.4, 0.38, 50), np.random.normal(2.8, 0.31, 50), np.random.normal(3.0, 0.32, 50)]
)

petal_length = np.concatenate(
    [np.random.normal(1.5, 0.17, 50), np.random.normal(4.3, 0.47, 50), np.random.normal(5.6, 0.55, 50)]
)

petal_width = np.concatenate(
    [np.random.normal(0.2, 0.10, 50), np.random.normal(1.3, 0.20, 50), np.random.normal(2.0, 0.27, 50)]
)

variables = [sepal_length, sepal_width, petal_length, petal_width]
var_names = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]
n_vars = len(variables)

# Create scatter matrix grid
cell_size = 900
grid = []

for i in range(n_vars):
    row = []
    for j in range(n_vars):
        x_label = var_names[j] if i == n_vars - 1 else ""
        y_label = var_names[i] if j == 0 else ""

        if i == j:
            # Diagonal: Histogram
            p = figure(width=cell_size, height=cell_size, x_axis_label=x_label, y_axis_label=y_label, tools="")

            hist_data = variables[i]
            bins = np.linspace(hist_data.min() - 0.1, hist_data.max() + 0.1, 20)

            for k, sp in enumerate(species_list):
                mask = species == sp
                hist, edges = np.histogram(hist_data[mask], bins=bins)
                source = ColumnDataSource(data={"top": hist, "left": edges[:-1], "right": edges[1:]})
                p.quad(
                    top="top",
                    bottom=0,
                    left="left",
                    right="right",
                    source=source,
                    fill_color=IMPRINT[k],
                    line_color=PAGE_BG,
                    line_width=1.5,
                    alpha=0.7,
                    legend_label=sp.capitalize(),
                )

            p.y_range.start = 0
            if i == 0:
                p.legend.location = "top_right"
                p.legend.label_text_font_size = "16pt"
                p.legend.glyph_height = 20
                p.legend.glyph_width = 20
                p.legend.spacing = 8
            else:
                p.legend.visible = False

        else:
            # Off-diagonal: Scatter plot with refined styling
            source = ColumnDataSource(data={"x": variables[j], "y": variables[i], "species": species})

            p = figure(width=cell_size, height=cell_size, x_axis_label=x_label, y_axis_label=y_label, tools="")

            p.scatter(
                x="x",
                y="y",
                source=source,
                size=14,
                alpha=0.65,
                fill_color=factor_cmap("species", IMPRINT, species_list),
                line_color="white" if THEME == "light" else "#2A2A27",
                line_width=0.8,
            )

        # Style axes — minimal, refined aesthetic
        p.background_fill_color = PAGE_BG
        p.border_fill_color = PAGE_BG
        p.outline_line_width = 0  # Remove spines for cleaner look

        p.title.text_color = INK
        p.xaxis.axis_label_text_color = INK
        p.yaxis.axis_label_text_color = INK
        p.xaxis.major_label_text_color = INK_SOFT
        p.yaxis.major_label_text_color = INK_SOFT
        p.xaxis.axis_line_color = INK_SOFT
        p.yaxis.axis_line_color = INK_SOFT
        p.xaxis.major_tick_line_color = INK_SOFT
        p.yaxis.major_tick_line_color = INK_SOFT
        p.xaxis.major_tick_line_width = 1
        p.yaxis.major_tick_line_width = 1

        p.xaxis.axis_label_text_font_size = "20pt"
        p.yaxis.axis_label_text_font_size = "20pt"
        p.xaxis.major_label_text_font_size = "16pt"
        p.yaxis.major_label_text_font_size = "16pt"

        p.xgrid.grid_line_color = INK
        p.ygrid.grid_line_color = INK
        p.xgrid.grid_line_alpha = 0.08
        p.ygrid.grid_line_alpha = 0.08

        if p.legend:
            p.legend.background_fill_color = ELEVATED_BG
            p.legend.border_line_color = INK_SOFT
            p.legend.label_text_color = INK_SOFT
            p.legend.border_line_width = 1
            p.legend.label_text_font_size = "16pt"

        row.append(p)

    grid.append(row)

# Add title
grid[0][0].add_layout(
    Title(text="scatter-matrix · bokeh · anyplot.ai", text_font_size="28pt", align="left", text_color=INK), "above"
)

# Create grid layout
layout = gridplot(grid, toolbar_location=None, merge_tools=False)

# Save HTML
output_file(f"plot-{THEME}.html")
save(layout)

# Screenshot with headless Chrome
W, H = 3600, 3600
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
