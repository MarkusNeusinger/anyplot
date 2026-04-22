""" pyplots.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource, Div
from bokeh.plotting import figure
from sklearn.datasets import load_iris


# Data - Iris dataset
np.random.seed(42)
iris = load_iris()
df = pd.DataFrame(iris.data, columns=["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"])
df["species"] = [iris.target_names[t] for t in iris.target]

# Use 4 variables for the scatter matrix
variables = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]
n_vars = len(variables)

# Color mapping for species
color_map = {"setosa": "#306998", "versicolor": "#FFD43B", "virginica": "#4CAF50"}
df["color"] = df["species"].map(color_map)

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

# Column name mapping for the source
col_map = {
    "Sepal Length": "sepal_length",
    "Sepal Width": "sepal_width",
    "Petal Length": "petal_length",
    "Petal Width": "petal_width",
}

# Title
title_div = Div(
    text="<h1 style='text-align: center; font-size: 28pt; margin: 20px 0;'>scatter-matrix-interactive · bokeh · pyplots.ai</h1>",
    width=3600,
)

# Create grid of plots
plots = []
cell_size = 900  # Each cell 900x900, total ~3600x3600 for 4x4 grid

# Common tools (using string names for proper active_drag)
TOOLS = "box_select,pan,wheel_zoom,reset"

for i, var_y in enumerate(variables):
    row = []
    for j, var_x in enumerate(variables):
        # Create figure with box_select as default active tool
        p = figure(width=cell_size, height=cell_size, tools=TOOLS, active_drag="box_select")

        if i == j:
            # Diagonal - histogram
            hist, edges = np.histogram(df[var_x], bins=20)
            p.quad(
                top=hist,
                bottom=0,
                left=edges[:-1],
                right=edges[1:],
                fill_color="#306998",
                line_color="white",
                alpha=0.7,
            )
            # Add variable name as title in diagonal
            p.title.text = var_x
            p.title.text_font_size = "22pt"
            p.title.align = "center"
        else:
            # Off-diagonal - scatter plot with linked selection
            p.scatter(
                x=col_map[var_x],
                y=col_map[var_y],
                source=source,
                size=15,
                fill_color="color",
                line_color="white",
                line_width=1,
                alpha=0.7,
                selection_fill_alpha=0.9,
                selection_line_color="black",
                selection_line_width=2,
                nonselection_fill_alpha=0.15,
                nonselection_fill_color="gray",
                nonselection_line_color="gray",
                nonselection_line_alpha=0.3,
            )

        # Axis labels - only on edges
        if i == n_vars - 1:  # Bottom row
            p.xaxis.axis_label = var_x + " (cm)"
            p.xaxis.axis_label_text_font_size = "18pt"
        else:
            p.xaxis.visible = False

        if j == 0:  # Left column
            p.yaxis.axis_label = var_y + " (cm)"
            p.yaxis.axis_label_text_font_size = "18pt"
        else:
            p.yaxis.visible = False

        # Tick label sizes
        p.xaxis.major_label_text_font_size = "16pt"
        p.yaxis.major_label_text_font_size = "16pt"

        # Grid styling
        p.xgrid.grid_line_alpha = 0.3
        p.ygrid.grid_line_alpha = 0.3

        row.append(p)
    plots.append(row)

# Add legend to top-right scatter plot
for species, color in color_map.items():
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
        line_color="white",
        alpha=0.9,
        legend_label=species.capitalize(),
    )

plots[0][1].legend.location = "top_right"
plots[0][1].legend.label_text_font_size = "16pt"
plots[0][1].legend.background_fill_alpha = 0.8

# Create grid layout
grid = gridplot(plots, merge_tools=True, toolbar_location="right")

# Combine title and grid
layout = column(title_div, grid)

# Save as PNG
export_png(layout, filename="plot.png")

# Save interactive HTML version
save(layout, filename="plot.html", title="scatter-matrix-interactive · bokeh · pyplots.ai")
