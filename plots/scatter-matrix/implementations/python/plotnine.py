""" anyplot.ai
scatter-matrix: Scatter Plot Matrix
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_grid,
    geom_density,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Iris-like data for multivariate visualization
np.random.seed(42)

species = np.repeat(["setosa", "versicolor", "virginica"], 50)

data = {
    "Sepal Length (cm)": np.concatenate(
        [np.random.normal(5.0, 0.35, 50), np.random.normal(5.9, 0.5, 50), np.random.normal(6.6, 0.6, 50)]
    ),
    "Sepal Width (cm)": np.concatenate(
        [np.random.normal(3.4, 0.4, 50), np.random.normal(2.8, 0.3, 50), np.random.normal(3.0, 0.3, 50)]
    ),
    "Petal Length (cm)": np.concatenate(
        [np.random.normal(1.5, 0.2, 50), np.random.normal(4.3, 0.5, 50), np.random.normal(5.5, 0.5, 50)]
    ),
    "Petal Width (cm)": np.concatenate(
        [np.random.normal(0.25, 0.1, 50), np.random.normal(1.3, 0.2, 50), np.random.normal(2.0, 0.3, 50)]
    ),
    "Species": species,
}

df = pd.DataFrame(data)

variables = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]

# Create long-form data for faceted scatter matrix
scatter_data = []
for var_y in variables:
    for var_x in variables:
        for idx in range(len(df)):
            scatter_data.append(
                {
                    "x": df[var_x].iloc[idx],
                    "y": df[var_y].iloc[idx],
                    "var_x": var_x,
                    "var_y": var_y,
                    "Species": df["Species"].iloc[idx],
                    "is_diag": var_x == var_y,
                }
            )

plot_df = pd.DataFrame(scatter_data)

# Set categorical type with explicit order for consistent row/column ordering
plot_df["var_x"] = pd.Categorical(plot_df["var_x"], categories=variables, ordered=True)
plot_df["var_y"] = pd.Categorical(plot_df["var_y"], categories=variables, ordered=True)

scatter_df = plot_df[~plot_df["is_diag"]]
diag_df = plot_df[plot_df["is_diag"]]

# Theme-adaptive styling
anyplot_theme = theme(
    figure_size=(14, 14),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_blank(),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.4),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.4),
    axis_ticks=element_line(color=INK_SOFT, size=0.3),
    plot_title=element_text(size=22, face="bold", ha="center", color=INK),
    strip_text_x=element_text(size=13, face="bold", color=INK),
    strip_text_y=element_text(size=13, face="bold", angle=0, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.4),
    legend_text=element_text(size=13, color=INK_SOFT),
    legend_title=element_text(size=14, color=INK),
    legend_position="right",
    panel_spacing=0.12,
    axis_title_x=element_blank(),
    axis_title_y=element_blank(),
)

# Create scatter matrix using facet_grid
plot = (
    ggplot(scatter_df, aes(x="x", y="y", color="Species"))
    + geom_point(size=3.5, alpha=0.7)
    + geom_density(aes(x="x", fill="Species", color="Species"), data=diag_df, alpha=0.4)
    + facet_grid("var_y ~ var_x", scales="free", labeller="label_value")
    + scale_color_manual(values=IMPRINT)
    + scale_fill_manual(values=IMPRINT)
    + labs(title="scatter-matrix · plotnine · anyplot.ai", x="", y="")
    + theme_minimal()
    + anyplot_theme
)

# Save the plot
plot.save(f"plot-{THEME}.png", dpi=300, width=14, height=14, verbose=False)
