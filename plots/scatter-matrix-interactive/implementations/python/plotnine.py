""" anyplot.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-18
"""

import os
import sys


sys.path.pop(0)

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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (first series #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: Iris dataset for multivariate analysis
iris = load_iris()
df = pd.DataFrame(iris.data, columns=["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"])
df["Species"] = pd.Categorical([iris.target_names[i] for i in iris.target])

variables = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]

# Create long-form data for scatter matrix
scatter_data = []
density_data = []

for i, var_y in enumerate(variables):
    for j, var_x in enumerate(variables):
        if i == j:
            # Diagonal: histogram-based density
            var_min, var_max = df[var_x].min(), df[var_x].max()
            var_range = var_max - var_min
            baseline = var_min

            for species in df["Species"].unique():
                species_vals = df[df["Species"] == species][var_x].values
                hist, edges = np.histogram(species_vals, bins=20, range=(var_min, var_max), density=True)
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
            # Off-diagonal: scatter points
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

# Create scatter plot matrix
plot = (
    ggplot(mapping=aes(x="x"))
    + geom_point(data=scatter_df, mapping=aes(y="y", color="Species"), size=3.5, alpha=0.7)
    + geom_ribbon(data=density_df, mapping=aes(ymin="ymin", ymax="ymax", fill="Species"), alpha=0.5)
    + facet_grid("var_y ~ var_x", scales="free")
    + scale_color_manual(values=IMPRINT)
    + scale_fill_manual(values=IMPRINT)
    + labs(title="scatter-matrix-interactive · python · plotnine · anyplot.ai", x="", y="")
    + theme_minimal()
    + theme(
        figure_size=(16, 16),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK_MUTED, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK_MUTED, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        plot_title=element_text(size=24, color=INK, ha="left", weight="bold"),
        strip_text_x=element_text(size=16, color=INK),
        strip_text_y=element_text(size=16, color=INK, angle=0),
        axis_text=element_text(size=14, color=INK_SOFT),
        axis_title_x=element_text(size=16, color=INK),
        axis_title_y=element_text(size=16, color=INK),
        legend_title=element_text(size=16, color=INK),
        legend_text=element_text(size=14, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),
        legend_position="bottom",
        panel_spacing=0.03,
    )
)

# Save plot
plot.save(f"plot-{THEME}.png", dpi=300, width=16, height=16, verbose=False)
