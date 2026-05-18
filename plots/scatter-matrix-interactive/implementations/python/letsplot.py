""" anyplot.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_histogram,
    geom_point,
    ggbunch,
    ggplot,
    ggsave,
    ggsize,
    ggtitle,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series (#009E73) is always first
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2"]

# Data - Synthetic iris-like dataset (4 numeric variables, 150 points)
np.random.seed(42)

n_per_species = 50

species_a = pd.DataFrame(
    {
        "Sepal Length": np.random.normal(5.0, 0.35, n_per_species),
        "Sepal Width": np.random.normal(3.4, 0.38, n_per_species),
        "Petal Length": np.random.normal(1.5, 0.17, n_per_species),
        "Petal Width": np.random.normal(0.25, 0.10, n_per_species),
        "Species": "Setosa",
    }
)

base_b = np.random.normal(0, 1, n_per_species)
species_b = pd.DataFrame(
    {
        "Sepal Length": 5.9 + 0.5 * base_b + np.random.normal(0, 0.2, n_per_species),
        "Sepal Width": 2.8 + 0.3 * base_b + np.random.normal(0, 0.2, n_per_species),
        "Petal Length": 4.3 + 0.5 * base_b + np.random.normal(0, 0.3, n_per_species),
        "Petal Width": 1.3 + 0.2 * base_b + np.random.normal(0, 0.15, n_per_species),
        "Species": "Versicolor",
    }
)

base_c = np.random.normal(0, 1, n_per_species)
species_c = pd.DataFrame(
    {
        "Sepal Length": 6.6 + 0.6 * base_c + np.random.normal(0, 0.3, n_per_species),
        "Sepal Width": 3.0 + 0.3 * base_c + np.random.normal(0, 0.25, n_per_species),
        "Petal Length": 5.6 + 0.6 * base_c + np.random.normal(0, 0.3, n_per_species),
        "Petal Width": 2.0 + 0.3 * base_c + np.random.normal(0, 0.2, n_per_species),
        "Species": "Virginica",
    }
)

df = pd.concat([species_a, species_b, species_c], ignore_index=True)

variables = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]
n = len(variables)

# Create individual plots for the 4x4 matrix
plots = []
for i, var_y in enumerate(variables):
    for j, var_x in enumerate(variables):
        show_x_label = i == n - 1
        show_y_label = j == 0

        if i == j:
            # Diagonal: histogram showing distribution
            p = (
                ggplot(df, aes(x=var_x, fill="Species"))
                + geom_histogram(alpha=0.7, bins=15, position="identity")
                + scale_fill_manual(values=OKABE_ITO)
                + labs(x=var_x if show_x_label else "", y="")
                + theme_minimal()
                + theme(
                    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
                    panel_background=element_rect(fill=PAGE_BG),
                    panel_grid_major=element_line(color=INK, size=0.2),
                    axis_title_x=element_text(size=16, color=INK) if show_x_label else element_blank(),
                    axis_title_y=element_blank(),
                    axis_text=element_text(size=13, color=INK_SOFT),
                    axis_line=element_line(color=INK_SOFT, size=0.3),
                    legend_position="none",
                    plot_margin=[5, 5, 5, 5],
                )
            )
        else:
            # Off-diagonal: scatter plot with tooltips for interactivity
            p = (
                ggplot(df, aes(x=var_x, y=var_y, color="Species", fill="Species"))
                + geom_point(
                    size=4,
                    alpha=0.7,
                    shape=21,
                    tooltips=layer_tooltips()
                    .line("Species: @Species")
                    .line(f"{var_x}: @{{{var_x}}}")
                    .line(f"{var_y}: @{{{var_y}}}"),
                )
                + scale_color_manual(values=OKABE_ITO)
                + scale_fill_manual(values=OKABE_ITO)
                + labs(x=var_x if show_x_label else "", y=var_y if show_y_label else "")
                + theme_minimal()
                + theme(
                    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
                    panel_background=element_rect(fill=PAGE_BG),
                    panel_grid_major=element_line(color=INK, size=0.2),
                    axis_title_x=element_text(size=16, color=INK) if show_x_label else element_blank(),
                    axis_title_y=element_text(size=16, color=INK) if show_y_label else element_blank(),
                    axis_text=element_text(size=13, color=INK_SOFT),
                    axis_line=element_line(color=INK_SOFT, size=0.3),
                    legend_position="none",
                    plot_margin=[5, 5, 5, 5],
                )
            )
        plots.append(p)

# Calculate regions for ggbunch
title_height = 0.06
legend_height = 0.06
grid_height = 1.0 - title_height - legend_height
cell_size = grid_height / n

# Title plot
title_df = pd.DataFrame({"x": [0], "y": [0]})
title_plot = (
    ggplot(title_df, aes(x="x", y="y"))
    + geom_point(alpha=0)
    + ggtitle("scatter-matrix-interactive · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=32, color=INK, hjust=0.5),
        axis_line=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_title=element_blank(),
        panel_grid=element_blank(),
    )
)

# Legend plot
legend_df = pd.DataFrame({"x": [1, 2, 3], "y": [0, 0, 0], "Species": ["Setosa", "Versicolor", "Virginica"]})
legend_plot = (
    ggplot(legend_df, aes(x="x", y="y", color="Species", fill="Species"))
    + geom_point(size=6, shape=21, alpha=0.8)
    + scale_color_manual(values=OKABE_ITO)
    + scale_fill_manual(values=OKABE_ITO)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="bottom",
        legend_direction="horizontal",
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_title=element_blank(),
        panel_grid=element_blank(),
    )
)

# Build final layout
final_plots = [title_plot]
final_plots.extend(plots)
final_plots.append(legend_plot)

final_regions = []
final_regions.append((0, 0, 1, title_height, 0, 0))

for idx in range(n * n):
    row = idx // n
    col = idx % n
    x = col * cell_size + 0.02
    y = title_height + row * cell_size
    final_regions.append((x, y, cell_size, cell_size, 0, 0))

final_regions.append((0.25, 1.0 - legend_height, 0.5, legend_height, 0, 0))

# Combine all plots
final_plot = ggbunch(final_plots, final_regions) + ggsize(1600, 1600)

# Save output
ggsave(final_plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(final_plot, f"plot-{THEME}.html", path=".")
