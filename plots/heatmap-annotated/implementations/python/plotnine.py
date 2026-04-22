""" pyplots.ai
heatmap-annotated: Annotated Heatmap
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_distiller,
    theme,
    theme_minimal,
)


# Data: Correlation matrix of economic indicators
np.random.seed(42)
variables = [
    "GDP Growth",
    "Inflation",
    "Unemployment",
    "Interest Rate",
    "Consumer Conf",
    "Mfg Index",
    "Export Vol",
    "Housing",
]

n_vars = len(variables)

# Generate a realistic correlation matrix
base = np.random.randn(n_vars, n_vars)
corr_matrix = np.dot(base, base.T)
d = np.sqrt(np.diag(corr_matrix))
corr_matrix = corr_matrix / d[:, None] / d[None, :]
np.fill_diagonal(corr_matrix, 1.0)
corr_matrix = (corr_matrix + corr_matrix.T) / 2  # Ensure symmetry

# Create DataFrame in long format for plotnine
rows = []
for i, row_var in enumerate(variables):
    for j, col_var in enumerate(variables):
        rows.append({"x": col_var, "y": row_var, "value": corr_matrix[i, j]})

df = pd.DataFrame(rows)

# Convert to categorical to preserve order
df["x"] = pd.Categorical(df["x"], categories=variables, ordered=True)
df["y"] = pd.Categorical(df["y"], categories=variables[::-1], ordered=True)

# Determine text color based on background
df["text_color"] = df["value"].apply(lambda v: "white" if abs(v) > 0.5 else "black")

# Create the annotated heatmap
plot = (
    ggplot(df, aes(x="x", y="y", fill="value"))
    + geom_tile(color="white", size=0.5)
    + geom_text(aes(label="value", color="text_color"), format_string="{:.2f}", size=12)
    + scale_fill_distiller(type="div", palette="RdBu", limits=(-1, 1), name="Correlation")
    + labs(x="Variable", y="Variable", title="heatmap-annotated · plotnine · pyplots.ai")
    + coord_fixed(ratio=1)
    + theme_minimal()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center"),
        axis_title=element_text(size=20),
        axis_text_x=element_text(size=14, rotation=45, ha="right"),
        axis_text_y=element_text(size=14),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
    )
)

# Apply identity scale for text color
plot = plot + scale_color_identity()

# Save
plot.save("plot.png", dpi=300, width=12, height=12)
