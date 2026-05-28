""" anyplot.ai
scatter-matrix: Scatter Plot Matrix
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd

from lets_plot import *  # noqa: F403, F405
from lets_plot.export import ggsave

LetsPlot.setup_html()  # noqa: F405

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Iris-like dataset with 4 variables
np.random.seed(42)
n = 150

species = np.repeat(["Setosa", "Versicolor", "Virginica"], n // 3)

sepal_length_setosa = np.random.normal(5.0, 0.35, n // 3)
sepal_width_setosa = np.random.normal(3.4, 0.38, n // 3)
petal_length_setosa = np.random.normal(1.5, 0.17, n // 3)
petal_width_setosa = np.random.normal(0.25, 0.1, n // 3)

sepal_length_versicolor = np.random.normal(5.9, 0.52, n // 3)
sepal_width_versicolor = np.random.normal(2.8, 0.31, n // 3)
petal_length_versicolor = np.random.normal(4.3, 0.47, n // 3)
petal_width_versicolor = np.random.normal(1.3, 0.2, n // 3)

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

# Build list of plots and their regions for ggbunch
plots = []
regions = []

# Calculate cell dimensions
margin_top = 0.08
margin_bottom = 0.08
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
                ggplot(df_plot, aes(x=var_x, fill="Species"))
                + geom_histogram(alpha=0.7, bins=15, position="identity")
                + scale_fill_manual(values=IMPRINT)
                + theme_minimal()
                + theme(
                    axis_title=element_blank(),
                    axis_text=element_text(size=14, color=INK_SOFT),
                    legend_position="none",
                    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
                    panel_background=element_rect(fill=PAGE_BG),
                    panel_grid_minor=element_blank(),
                    panel_grid_major=element_line(color=INK_SOFT, size=0.2),
                )
            )
        else:
            # Off-diagonal: scatter plot
            p = (
                ggplot(df_plot, aes(x=var_x, y=var_y, color="Species"))
                + geom_point(size=3.5, alpha=0.7)
                + scale_color_manual(values=IMPRINT)
                + theme_minimal()
                + theme(
                    axis_title=element_blank(),
                    axis_text=element_text(size=14, color=INK_SOFT),
                    legend_position="none",
                    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
                    panel_background=element_rect(fill=PAGE_BG),
                    panel_grid_minor=element_blank(),
                    panel_grid_major=element_line(color=INK_SOFT, size=0.2),
                )
            )

        # Add variable names on bottom edge (last row)
        if i == n_vars - 1:
            p = p + labs(x=var_x) + theme(axis_title_x=element_text(size=18, color=INK))

        # Add variable names on left edge (first column)
        if j == 0:
            p = p + labs(y=var_y) + theme(axis_title_y=element_text(size=18, color=INK))

        plots.append(p)
        x_pos = margin_left + j * cell_width
        y_pos = margin_top + i * cell_height
        regions.append((x_pos, y_pos, cell_width, cell_height, 0, 0))

# Create title plot
title_plot = (
    ggplot()
    + geom_blank()
    + ggtitle("scatter-matrix · letsplot · anyplot.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=32, hjust=0.5, face="bold", color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)
plots.append(title_plot)
regions.append((0, 0, 1, margin_top, 0, 0))

# Create legend plot
legend_df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 2, 3], "Species": ["Setosa", "Versicolor", "Virginica"]})
legend_plot = (
    ggplot(legend_df, aes(x="x", y="y", color="Species"))
    + geom_point(size=8)
    + scale_color_manual(values=IMPRINT)
    + theme_void()
    + theme(
        legend_position="bottom",
        legend_title=element_text(size=20, color=INK),
        legend_text=element_text(size=18, color=INK_SOFT),
        legend_direction="horizontal",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
    + guides(color=guide_legend(override_aes={"size": 10}))
)
plots.append(legend_plot)
regions.append((0.2, 1.0 - margin_bottom, 0.6, margin_bottom, 0, 0))

# Combine into ggbunch with square format
combined = ggbunch(plots, regions) + ggsize(1200, 1200)

# Save with scale for high resolution (target ~3600x3600)
ggsave(combined, filename=f"plot-{THEME}.png", path=".", scale=3)
ggsave(combined, filename=f"plot-{THEME}.html", path=".")
