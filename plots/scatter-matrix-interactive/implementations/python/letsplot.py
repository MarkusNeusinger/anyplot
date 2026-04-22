""" pyplots.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 78/100 | Created: 2026-01-10
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
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

# Data - Synthetic iris-like dataset (4 numeric variables, 150 points)
np.random.seed(42)

# Generate measurements for three plant species with realistic correlations
n_per_species = 50

# Species A (small flowers): lower values
species_a = pd.DataFrame(
    {
        "Sepal Length (cm)": np.random.normal(5.0, 0.35, n_per_species),
        "Sepal Width (cm)": np.random.normal(3.4, 0.38, n_per_species),
        "Petal Length (cm)": np.random.normal(1.5, 0.17, n_per_species),
        "Petal Width (cm)": np.random.normal(0.25, 0.10, n_per_species),
        "Species": "Setosa",
    }
)

# Species B (medium flowers): intermediate values with correlation
base_b = np.random.normal(0, 1, n_per_species)
species_b = pd.DataFrame(
    {
        "Sepal Length (cm)": 5.9 + 0.5 * base_b + np.random.normal(0, 0.2, n_per_species),
        "Sepal Width (cm)": 2.8 + 0.3 * base_b + np.random.normal(0, 0.2, n_per_species),
        "Petal Length (cm)": 4.3 + 0.5 * base_b + np.random.normal(0, 0.3, n_per_species),
        "Petal Width (cm)": 1.3 + 0.2 * base_b + np.random.normal(0, 0.15, n_per_species),
        "Species": "Versicolor",
    }
)

# Species C (large flowers): higher values with strong correlation
base_c = np.random.normal(0, 1, n_per_species)
species_c = pd.DataFrame(
    {
        "Sepal Length (cm)": 6.6 + 0.6 * base_c + np.random.normal(0, 0.3, n_per_species),
        "Sepal Width (cm)": 3.0 + 0.3 * base_c + np.random.normal(0, 0.25, n_per_species),
        "Petal Length (cm)": 5.6 + 0.6 * base_c + np.random.normal(0, 0.3, n_per_species),
        "Petal Width (cm)": 2.0 + 0.3 * base_c + np.random.normal(0, 0.2, n_per_species),
        "Species": "Virginica",
    }
)

df = pd.concat([species_a, species_b, species_c], ignore_index=True)

# Variables for the scatter matrix (use shorter labels for axis to prevent truncation)
variables = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]
short_labels = ["Sepal Len.", "Sepal Wid.", "Petal Len.", "Petal Wid."]
n = len(variables)

# Color palette - accessible colors with good contrast on white background
colors = ["#306998", "#E67E22", "#16A085"]

# Create individual plots for the 4x4 matrix
plots = []
for i, var_y in enumerate(variables):
    for j, var_x in enumerate(variables):
        # Only show axis labels on edges (bottom row for x, left column for y)
        show_x_label = i == n - 1
        show_y_label = j == 0

        # Get short labels for axes
        x_label = short_labels[j]
        y_label = short_labels[i]

        if i == j:
            # Diagonal: histogram showing distribution
            p = (
                ggplot(df, aes(x=var_x, fill="Species"))
                + geom_histogram(alpha=0.7, bins=15, position="identity")
                + scale_fill_manual(values=colors)
                + labs(x=x_label if show_x_label else "", y="")
                + theme_minimal()
                + theme(
                    axis_title_x=element_text(size=16) if show_x_label else element_blank(),
                    axis_title_y=element_blank(),
                    axis_text=element_text(size=13),
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
                + scale_color_manual(values=colors)
                + scale_fill_manual(values=colors)
                + labs(x=x_label if show_x_label else "", y=y_label if show_y_label else "")
                + theme_minimal()
                + theme(
                    axis_title_x=element_text(size=16) if show_x_label else element_blank(),
                    axis_title_y=element_text(size=16) if show_y_label else element_blank(),
                    axis_text=element_text(size=13),
                    legend_position="none",
                    plot_margin=[5, 5, 5, 5],
                )
            )
        plots.append(p)

# Calculate regions for ggbunch (4x4 grid)
# Leave space for title at top and legend at bottom
title_height = 0.06
legend_height = 0.06
grid_height = 1.0 - title_height - legend_height
cell_size = grid_height / n

# Title plot - needs a geom layer for lets-plot (use middle dot character)
title_df = pd.DataFrame({"x": [0], "y": [0]})
title_plot = (
    ggplot(title_df, aes(x="x", y="y"))
    + geom_point(alpha=0)  # Invisible point to satisfy lets-plot layer requirement
    + ggtitle("scatter-matrix-interactive \u00b7 letsplot \u00b7 pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=32, hjust=0.5),
        axis_line=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_title=element_blank(),
        panel_grid=element_blank(),
    )
)

# Legend plot - separate plot for better control over legend text
legend_df = pd.DataFrame({"x": [1, 2, 3], "y": [0, 0, 0], "Species": ["Setosa", "Versicolor", "Virginica"]})
legend_plot = (
    ggplot(legend_df, aes(x="x", y="y", color="Species", fill="Species"))
    + geom_point(size=6, shape=21, alpha=0.8)
    + scale_color_manual(values=colors)
    + scale_fill_manual(values=colors)
    + theme_minimal()
    + theme(
        legend_position="bottom",
        legend_direction="horizontal",
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        axis_line=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_title=element_blank(),
        panel_grid=element_blank(),
    )
)

# Build final layout: title + matrix + legend
final_plots = [title_plot]
final_plots.extend(plots)
final_plots.append(legend_plot)

# Define regions for ggbunch
final_regions = []

# Title region (top)
final_regions.append((0, 0, 1, title_height, 0, 0))

# Matrix regions (4x4 grid) - slightly offset from left edge
for idx in range(n * n):
    row = idx // n
    col = idx % n
    x = col * cell_size + 0.02
    y = title_height + row * cell_size
    final_regions.append((x, y, cell_size, cell_size, 0, 0))

# Legend region (bottom center)
final_regions.append((0.25, 1.0 - legend_height, 0.5, legend_height, 0, 0))

# Combine all plots using ggbunch with square aspect ratio
final_plot = ggbunch(final_plots, final_regions) + ggsize(1200, 1200)

# Save output to current directory (PNG only)
ggsave(final_plot, "plot.png", path=".", scale=3)
