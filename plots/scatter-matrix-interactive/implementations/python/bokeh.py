""" anyplot.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-18
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource, Div, HoverTool
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import load_iris


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Iris dataset
iris = load_iris()
df = pd.DataFrame(iris.data, columns=["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"])
df["species"] = [iris.target_names[t] for t in iris.target]

# Color mapping for species using Okabe-Ito
species_names = ["setosa", "versicolor", "virginica"]
color_map = {name: OKABE_ITO[i] for i, name in enumerate(species_names)}
df["color"] = df["species"].map(color_map)

# Use 4 variables for the scatter matrix
variables = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]
n_vars = len(variables)

# Create a shared ColumnDataSource for linked brushing
source = ColumnDataSource(
    data={
        "sepal_length": df["Sepal Length"],
        "sepal_width": df["Sepal Width"],
        "petal_length": df["Petal Length"],
        "petal_width": df["Petal Width"],
        "color": df["color"],
        "species": df["species"],
    }
)

# Column name mapping
col_map = {
    "Sepal Length": "sepal_length",
    "Sepal Width": "sepal_width",
    "Petal Length": "petal_length",
    "Petal Width": "petal_width",
}

# Create grid of plots
plots = []
cell_size = 900  # Each cell 900x900, total ~3600x3600 for 4x4 grid

TOOLS = "box_select,pan,wheel_zoom,reset"

for i, var_y in enumerate(variables):
    row = []
    for j, var_x in enumerate(variables):
        p = figure(width=cell_size, height=cell_size, tools=TOOLS, active_drag="box_select")

        # Set theme colors
        p.background_fill_color = PAGE_BG
        p.border_fill_color = PAGE_BG
        p.outline_line_color = INK_SOFT

        if i == j:
            # Diagonal - histogram
            hist, edges = np.histogram(df[var_x], bins=20)
            p.quad(
                top=hist,
                bottom=0,
                left=edges[:-1],
                right=edges[1:],
                fill_color=OKABE_ITO[0],
                line_color=PAGE_BG,
                alpha=0.7,
            )
            # Variable name as title
            p.title.text = var_x
            p.title.text_font_size = "22pt"
            p.title.text_color = INK
            p.title.align = "center"
        else:
            # Off-diagonal - scatter plot with linked selection
            p.scatter(
                x=col_map[var_x],
                y=col_map[var_y],
                source=source,
                size=15,
                fill_color="color",
                line_color=PAGE_BG,
                line_width=1,
                alpha=0.7,
                selection_fill_alpha=0.9,
                selection_line_color=INK,
                selection_line_width=2,
                nonselection_fill_alpha=0.15,
                nonselection_fill_color=INK_SOFT,
                nonselection_line_color=INK_SOFT,
                nonselection_line_alpha=0.3,
            )

            # Add hover tooltip
            hover = HoverTool(
                tooltips=[
                    ("Species", "@species"),
                    (f"{var_x}", f"@{col_map[var_x]}" + "{0.00}"),
                    (f"{var_y}", f"@{col_map[var_y]}" + "{0.00}"),
                ]
            )
            p.add_tools(hover)

        # Axis labels - only on edges
        if i == n_vars - 1:  # Bottom row
            p.xaxis.axis_label = var_x
            p.xaxis.axis_label_text_font_size = "22pt"
            p.xaxis.axis_label_text_color = INK
        else:
            p.xaxis.visible = False

        if j == 0:  # Left column
            p.yaxis.axis_label = var_y
            p.yaxis.axis_label_text_font_size = "22pt"
            p.yaxis.axis_label_text_color = INK
        else:
            p.yaxis.visible = False

        # Tick label styling
        p.xaxis.major_label_text_font_size = "18pt"
        p.yaxis.major_label_text_font_size = "18pt"
        p.xaxis.major_label_text_color = INK_SOFT
        p.yaxis.major_label_text_color = INK_SOFT

        # Axis line colors
        p.xaxis.axis_line_color = INK_SOFT
        p.yaxis.axis_line_color = INK_SOFT
        p.xaxis.major_tick_line_color = INK_SOFT
        p.yaxis.major_tick_line_color = INK_SOFT

        # Grid styling - subtle (10% opacity)
        p.xgrid.grid_line_color = INK
        p.ygrid.grid_line_color = INK
        p.xgrid.grid_line_alpha = 0.10
        p.ygrid.grid_line_alpha = 0.10

        row.append(p)
    plots.append(row)

# Add legend to top-right scatter plot
for _idx, (species, color) in enumerate(color_map.items()):
    species_source = ColumnDataSource(
        data={
            "x": df[df["species"] == species]["Sepal Width"].values[:1],
            "y": df[df["species"] == species]["Sepal Length"].values[:1],
        }
    )
    plots[0][1].scatter(
        x="x",
        y="y",
        source=species_source,
        size=15,
        fill_color=color,
        line_color=PAGE_BG,
        alpha=0.9,
        legend_label=species.capitalize(),
    )

plots[0][1].legend.location = "top_right"
plots[0][1].legend.label_text_font_size = "16pt"
plots[0][1].legend.background_fill_color = ELEVATED_BG
plots[0][1].legend.border_line_color = INK_SOFT
plots[0][1].legend.label_text_color = INK_SOFT

# Create grid layout
grid = gridplot(plots, merge_tools=True, toolbar_location="right")

# Title
title_div = Div(
    text=f"<h1 style='text-align: center; font-size: 28pt; margin: 20px 0; color: {INK};'>scatter-matrix-interactive · python · bokeh · anyplot.ai</h1>",
    width=3600,
)

# Combine title and grid
layout = column(title_div, grid)

# Save as HTML
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
