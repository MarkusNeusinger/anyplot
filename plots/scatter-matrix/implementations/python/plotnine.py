""" pyplots.ai
scatter-matrix: Scatter Plot Matrix
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-26
"""

import warnings

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
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


warnings.filterwarnings("ignore")

# Data - Iris-like data for multivariate visualization
np.random.seed(42)

species = np.repeat(["setosa", "versicolor", "virginica"], 50)

# Generate correlated data for each species with realistic iris measurements
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

# Variables for the matrix
variables = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]

# Create long-form data for faceted scatter matrix
# Use consistent ordering for both rows and columns
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

# Colors - Python Blue, Python Yellow, and complementary coral
colors = ["#306998", "#FFD43B", "#E07A5F"]

# Create scatter matrix using facet_grid
plot = (
    ggplot(scatter_df, aes(x="x", y="y", color="Species"))
    + geom_point(size=3.5, alpha=0.7)
    + geom_density(aes(x="x", fill="Species", color="Species"), data=diag_df, alpha=0.4)
    + facet_grid("var_y ~ var_x", scales="free", labeller="label_value")
    + scale_color_manual(values=colors)
    + scale_fill_manual(values=colors)
    + labs(title="scatter-matrix · plotnine · pyplots.ai", x="", y="")
    + theme_minimal()
    + theme(
        figure_size=(14, 14),
        plot_title=element_text(size=22, face="bold", ha="center"),
        strip_text_x=element_text(size=13, face="bold"),
        strip_text_y=element_text(size=13, face="bold", angle=0),
        axis_text=element_text(size=10),
        axis_text_x=element_text(size=9),
        legend_title=element_text(size=14),
        legend_text=element_text(size=13),
        legend_position="right",
        panel_spacing=0.12,
        axis_title_x=element_blank(),
        axis_title_y=element_blank(),
    )
)

# Save the plot
plot.save("plot.png", dpi=300, width=14, height=14, verbose=False)
