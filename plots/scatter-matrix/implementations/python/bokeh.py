""" pyplots.ai
scatter-matrix: Scatter Plot Matrix
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, Title
from bokeh.plotting import figure
from bokeh.transform import factor_cmap


# Data - Iris-like dataset with 4 variables and species groups
np.random.seed(42)

# Generate realistic iris-like measurements (3 species, 50 samples each)
species = np.repeat(["setosa", "versicolor", "virginica"], 50)

# Sepal Length (cm)
sepal_length = np.concatenate(
    [
        np.random.normal(5.0, 0.35, 50),  # setosa
        np.random.normal(5.9, 0.52, 50),  # versicolor
        np.random.normal(6.6, 0.64, 50),  # virginica
    ]
)

# Sepal Width (cm)
sepal_width = np.concatenate(
    [
        np.random.normal(3.4, 0.38, 50),  # setosa
        np.random.normal(2.8, 0.31, 50),  # versicolor
        np.random.normal(3.0, 0.32, 50),  # virginica
    ]
)

# Petal Length (cm)
petal_length = np.concatenate(
    [
        np.random.normal(1.5, 0.17, 50),  # setosa
        np.random.normal(4.3, 0.47, 50),  # versicolor
        np.random.normal(5.6, 0.55, 50),  # virginica
    ]
)

# Petal Width (cm)
petal_width = np.concatenate(
    [
        np.random.normal(0.2, 0.10, 50),  # setosa
        np.random.normal(1.3, 0.20, 50),  # versicolor
        np.random.normal(2.0, 0.27, 50),  # virginica
    ]
)

# Variables and labels
variables = [sepal_length, sepal_width, petal_length, petal_width]
var_names = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]
n_vars = len(variables)

# Color palette (Python Blue, Python Yellow, and colorblind-safe teal)
colors = ["#306998", "#FFD43B", "#2AA198"]
species_list = ["setosa", "versicolor", "virginica"]

# Create scatter matrix grid
cell_size = 900  # Each cell is 900x900 px for a 3600x3600 total (square format)
grid = []

for i in range(n_vars):
    row = []
    for j in range(n_vars):
        # Configure axes labels - only on bottom row (x) and left column (y)
        x_label = var_names[j] if i == n_vars - 1 else ""
        y_label = var_names[i] if j == 0 else ""

        if i == j:
            # Diagonal: Histogram
            p = figure(width=cell_size, height=cell_size, x_axis_label=x_label, y_axis_label=y_label, tools="")

            # Create histograms for each species
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
                    fill_color=colors[k],
                    line_color="white",
                    line_width=1.5,
                    alpha=0.7,
                    legend_label=sp.capitalize(),
                )

            # Style histogram
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
            # Off-diagonal: Scatter plot
            source = ColumnDataSource(data={"x": variables[j], "y": variables[i], "species": species})

            p = figure(width=cell_size, height=cell_size, x_axis_label=x_label, y_axis_label=y_label, tools="")

            p.scatter(
                x="x",
                y="y",
                source=source,
                size=14,
                alpha=0.7,
                fill_color=factor_cmap("species", colors, species_list),
                line_color="white",
                line_width=1,
            )

        # Style axes for readability at 3600x3600
        p.xaxis.axis_label_text_font_size = "20pt"
        p.yaxis.axis_label_text_font_size = "20pt"
        p.xaxis.major_label_text_font_size = "16pt"
        p.yaxis.major_label_text_font_size = "16pt"
        p.axis.axis_line_width = 2
        p.axis.major_tick_line_width = 2
        p.axis.minor_tick_line_width = 1
        p.grid.grid_line_alpha = 0.3
        p.grid.grid_line_dash = "dashed"
        p.outline_line_width = 2
        p.outline_line_color = "#444444"

        row.append(p)

    grid.append(row)

# Add title to top-left plot
grid[0][0].add_layout(Title(text="scatter-matrix · bokeh · pyplots.ai", text_font_size="28pt", align="left"), "above")

# Create grid layout
layout = gridplot(grid, toolbar_location=None, merge_tools=False)

# Save as PNG and HTML
export_png(layout, filename="plot.png")
output_file("plot.html")
save(layout)
