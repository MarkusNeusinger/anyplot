""" pyplots.ai
scatter-matrix: Scatter Plot Matrix
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Iris-like dataset with 4 variables
np.random.seed(42)
n = 150

# Create realistic flower measurement data with species groupings
species = np.repeat(["Setosa", "Versicolor", "Virginica"], n // 3)

# Setosa: smaller flowers
sepal_length_setosa = np.random.normal(5.0, 0.35, n // 3)
sepal_width_setosa = np.random.normal(3.4, 0.38, n // 3)
petal_length_setosa = np.random.normal(1.5, 0.17, n // 3)
petal_width_setosa = np.random.normal(0.25, 0.1, n // 3)

# Versicolor: medium flowers
sepal_length_versicolor = np.random.normal(5.9, 0.52, n // 3)
sepal_width_versicolor = np.random.normal(2.8, 0.31, n // 3)
petal_length_versicolor = np.random.normal(4.3, 0.47, n // 3)
petal_width_versicolor = np.random.normal(1.3, 0.2, n // 3)

# Virginica: larger flowers
sepal_length_virginica = np.random.normal(6.6, 0.64, n // 3)
sepal_width_virginica = np.random.normal(3.0, 0.32, n // 3)
petal_length_virginica = np.random.normal(5.5, 0.55, n // 3)
petal_width_virginica = np.random.normal(2.0, 0.27, n // 3)

df = pd.DataFrame(
    {
        "Sepal Length (cm)": np.concatenate([sepal_length_setosa, sepal_length_versicolor, sepal_length_virginica]),
        "Sepal Width (cm)": np.concatenate([sepal_width_setosa, sepal_width_versicolor, sepal_width_virginica]),
        "Petal Length (cm)": np.concatenate([petal_length_setosa, petal_length_versicolor, petal_length_virginica]),
        "Petal Width (cm)": np.concatenate([petal_width_setosa, petal_width_versicolor, petal_width_virginica]),
        "Species": species,
    }
)

# Shorten column names for better display
df_plot = df.rename(
    columns={
        "Sepal Length (cm)": "Sepal Len",
        "Sepal Width (cm)": "Sepal Wid",
        "Petal Length (cm)": "Petal Len",
        "Petal Width (cm)": "Petal Wid",
    }
)

variables = ["Sepal Len", "Sepal Wid", "Petal Len", "Petal Wid"]
n_vars = len(variables)

# Custom colors for species - Python Blue, Yellow, and accessible red
colors = ["#306998", "#FFD43B", "#DC2626"]

# Build list of plots and their regions for ggbunch
plots = []
regions = []

# Calculate cell dimensions (relative to full size)
margin_top = 0.08  # Space for title
margin_bottom = 0.08  # Space for legend
margin_left = 0.02
margin_right = 0.02
available_height = 1.0 - margin_top - margin_bottom
available_width = 1.0 - margin_left - margin_right
cell_width = available_width / n_vars
cell_height = available_height / n_vars

# Create plots for the matrix
for i, var_y in enumerate(variables):
    for j, var_x in enumerate(variables):
        if i == j:
            # Diagonal: histogram
            p = (
                ggplot(df_plot, aes(x=var_x, fill="Species"))  # noqa: F405
                + geom_histogram(alpha=0.7, bins=15, position="identity")  # noqa: F405
                + scale_fill_manual(values=colors)  # noqa: F405
                + theme_minimal()  # noqa: F405
                + theme(  # noqa: F405
                    axis_title=element_blank(),  # noqa: F405
                    axis_text=element_text(size=14),  # noqa: F405
                    legend_position="none",
                    plot_background=element_rect(fill="white"),  # noqa: F405
                    panel_grid_minor=element_blank(),  # noqa: F405
                )
            )
        else:
            # Off-diagonal: scatter plot
            p = (
                ggplot(df_plot, aes(x=var_x, y=var_y, color="Species"))  # noqa: F405
                + geom_point(size=3.5, alpha=0.7)  # noqa: F405
                + scale_color_manual(values=colors)  # noqa: F405
                + theme_minimal()  # noqa: F405
                + theme(  # noqa: F405
                    axis_title=element_blank(),  # noqa: F405
                    axis_text=element_text(size=14),  # noqa: F405
                    legend_position="none",
                    plot_background=element_rect(fill="white"),  # noqa: F405
                    panel_grid_minor=element_blank(),  # noqa: F405
                )
            )

        # Add variable names on bottom edge (last row)
        if i == n_vars - 1:
            p = (
                p
                + labs(x=var_x)  # noqa: F405
                + theme(  # noqa: F405
                    axis_title_x=element_text(size=18)  # noqa: F405
                )
            )

        # Add variable names on left edge (first column)
        if j == 0:
            p = (
                p
                + labs(y=var_y)  # noqa: F405
                + theme(  # noqa: F405
                    axis_title_y=element_text(size=18)  # noqa: F405
                )
            )

        plots.append(p)
        # Region: (x, y, width, height) - y from top
        x_pos = margin_left + j * cell_width
        y_pos = margin_top + i * cell_height
        regions.append((x_pos, y_pos, cell_width, cell_height, 0, 0))

# Create title plot
title_plot = (
    ggplot()  # noqa: F405
    + geom_blank()  # noqa: F405
    + ggtitle("scatter-matrix · letsplot · pyplots.ai")  # noqa: F405
    + theme_void()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=32, hjust=0.5, face="bold"),  # noqa: F405
        plot_background=element_rect(fill="white"),  # noqa: F405
    )
)
plots.append(title_plot)
regions.append((0, 0, 1, margin_top, 0, 0))

# Create legend plot
legend_df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 2, 3], "Species": ["Setosa", "Versicolor", "Virginica"]})
legend_plot = (
    ggplot(legend_df, aes(x="x", y="y", color="Species"))  # noqa: F405
    + geom_point(size=8)  # noqa: F405
    + scale_color_manual(values=colors)  # noqa: F405
    + theme_void()  # noqa: F405
    + theme(  # noqa: F405
        legend_position="bottom",
        legend_title=element_text(size=20),  # noqa: F405
        legend_text=element_text(size=18),  # noqa: F405
        legend_direction="horizontal",
        plot_background=element_rect(fill="white"),  # noqa: F405
    )
    + guides(color=guide_legend(override_aes={"size": 10}))  # noqa: F405
)
plots.append(legend_plot)
regions.append((0.2, 1.0 - margin_bottom, 0.6, margin_bottom, 0, 0))

# Combine into ggbunch with square format (3600x3600)
combined = ggbunch(plots, regions) + ggsize(1200, 1200)  # noqa: F405

# Save with scale for high resolution (target ~3600x3600)
export_ggsave(combined, filename="plot.png", path=".", scale=3)

# Also save HTML for interactive version
export_ggsave(combined, filename="plot.html", path=".")
