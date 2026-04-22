""" pyplots.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 72/100 | Created: 2026-01-10
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    facet_grid,
    geom_point,
    geom_ribbon,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)
from sklearn.datasets import load_iris


# Data: Iris dataset for multivariate analysis
np.random.seed(42)
iris = load_iris()
df = pd.DataFrame(iris.data, columns=["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"])
df["Species"] = pd.Categorical([iris.target_names[i] for i in iris.target])

# Variables for the matrix (already include units)
variables = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]

# Colorblind-safe palette (Dark2 inspired - teal, orange, purple)
colors = ["#1B9E77", "#D95F02", "#7570B3"]

# Create long-form data for scatter matrix
scatter_data = []
density_data = []

for i, var_y in enumerate(variables):
    for j, var_x in enumerate(variables):
        if i == j:
            # Diagonal: Create normalized density data that fits within the variable's range
            var_min, var_max = df[var_x].min(), df[var_x].max()
            var_range = var_max - var_min
            # Use baseline slightly above min for visual clarity
            baseline = var_min

            for species in df["Species"].unique():
                species_vals = df[df["Species"] == species][var_x].values
                # Simple histogram-based density
                hist, edges = np.histogram(species_vals, bins=20, range=(var_min, var_max), density=True)
                # Normalize to fit within the y-axis range (scale to var_range * 0.5)
                max_density = hist.max() if hist.max() > 0 else 1
                hist_scaled = hist / max_density * var_range * 0.5 + baseline
                bin_centers = (edges[:-1] + edges[1:]) / 2

                for k in range(len(bin_centers)):
                    density_data.append(
                        {
                            "x": bin_centers[k],
                            "ymin": baseline,
                            "ymax": hist_scaled[k],
                            "Species": species,
                            "var_x": var_x,
                            "var_y": var_y,
                        }
                    )
        else:
            # Off-diagonal: scatter data
            for _, row in df.iterrows():
                scatter_data.append(
                    {"x": row[var_x], "y": row[var_y], "Species": row["Species"], "var_x": var_x, "var_y": var_y}
                )

scatter_df = pd.DataFrame(scatter_data)
density_df = pd.DataFrame(density_data)

# Set factor levels for proper ordering
scatter_df["var_x"] = pd.Categorical(scatter_df["var_x"], categories=variables, ordered=True)
scatter_df["var_y"] = pd.Categorical(scatter_df["var_y"], categories=variables[::-1], ordered=True)
density_df["var_x"] = pd.Categorical(density_df["var_x"], categories=variables, ordered=True)
density_df["var_y"] = pd.Categorical(density_df["var_y"], categories=variables[::-1], ordered=True)

# Sort density data for proper ribbon rendering
density_df = density_df.sort_values(["var_x", "var_y", "Species", "x"])

# Create scatter plot matrix with density ribbons on diagonal
plot = (
    ggplot(mapping=aes(x="x"))
    + geom_point(data=scatter_df, mapping=aes(y="y", color="Species"), size=3.5, alpha=0.7)
    + geom_ribbon(data=density_df, mapping=aes(ymin="ymin", ymax="ymax", fill="Species"), alpha=0.5)
    + facet_grid("var_y ~ var_x", scales="free")
    + scale_color_manual(values=colors)
    + scale_fill_manual(values=colors)
    + labs(title="scatter-matrix-interactive · plotnine · pyplots.ai", x="", y="")
    + theme_minimal()
    + theme(
        figure_size=(16, 16),
        plot_title=element_text(size=24, weight="bold", ha="left"),
        strip_text_x=element_text(size=14),
        strip_text_y=element_text(size=14, angle=0),
        axis_text=element_text(size=11),
        axis_title_x=element_text(size=16),
        axis_title_y=element_text(size=16),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="bottom",
        legend_background=element_rect(fill="white", alpha=0.9),
        panel_spacing=0.03,
        panel_grid_major=element_line(color="#cccccc", alpha=0.3),
        panel_grid_minor=element_line(color="#eeeeee", alpha=0.2),
        panel_background=element_rect(fill="white"),
    )
)

# Save plot
plot.save("plot.png", dpi=300, width=16, height=16, verbose=False)
