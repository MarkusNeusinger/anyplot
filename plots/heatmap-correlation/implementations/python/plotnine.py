""" pyplots.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
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
    scale_fill_gradient2,
    theme,
    theme_minimal,
)


# Data - realistic financial/portfolio variables for correlation analysis
np.random.seed(42)

variables = ["Stock_A", "Stock_B", "Stock_C", "Bonds", "Gold", "Real_Estate", "Oil", "Tech_Index"]

# Create a realistic correlation matrix with varied correlations
# Demonstrates positive correlations (stocks), negative correlations (bonds vs stocks),
# and near-zero correlations (gold vs some assets)
base_corr = np.array(
    [
        [1.00, 0.85, 0.72, -0.35, -0.15, 0.42, 0.28, 0.91],  # Stock_A
        [0.85, 1.00, 0.68, -0.28, -0.22, 0.38, 0.31, 0.82],  # Stock_B
        [0.72, 0.68, 1.00, -0.18, -0.08, 0.52, 0.45, 0.75],  # Stock_C
        [-0.35, -0.28, -0.18, 1.00, 0.45, 0.12, -0.25, -0.32],  # Bonds
        [-0.15, -0.22, -0.08, 0.45, 1.00, 0.08, 0.35, -0.18],  # Gold
        [0.42, 0.38, 0.52, 0.12, 0.08, 1.00, 0.22, 0.48],  # Real_Estate
        [0.28, 0.31, 0.45, -0.25, 0.35, 0.22, 1.00, 0.32],  # Oil
        [0.91, 0.82, 0.75, -0.32, -0.18, 0.48, 0.32, 1.00],  # Tech_Index
    ]
)

# Convert matrix to long format for plotnine - use lower triangle only to reduce redundancy
rows = []
for i, var1 in enumerate(variables):
    for j, var2 in enumerate(variables):
        # Only include lower triangle (including diagonal)
        if i >= j:
            rows.append({"Var1": var1, "Var2": var2, "Correlation": base_corr[i, j]})

df = pd.DataFrame(rows)

# Set categorical order to maintain variable arrangement
df["Var1"] = pd.Categorical(df["Var1"], categories=variables, ordered=True)
df["Var2"] = pd.Categorical(df["Var2"], categories=variables, ordered=True)

# Create heatmap with lower triangle only
plot = (
    ggplot(df, aes(x="Var2", y="Var1", fill="Correlation"))
    + geom_tile(color="white", size=0.5)
    + geom_text(aes(label="Correlation"), format_string="{:.2f}", size=14, color="black")
    + scale_fill_gradient2(
        low="#2166AC",  # Blue for negative correlations
        mid="white",  # White for zero correlation
        high="#B2182B",  # Red for positive correlations
        midpoint=0,
        limits=(-1, 1),
        name="Correlation\nCoefficient",
    )
    + coord_fixed(ratio=1)
    + labs(title="heatmap-correlation · plotnine · pyplots.ai", x="Portfolio Asset", y="Portfolio Asset")
    + theme_minimal()
    + theme(
        figure_size=(12, 12),  # 12x12 at 300 DPI = 3600x3600 px
        plot_title=element_text(size=26, ha="center", weight="bold"),
        axis_title_x=element_text(size=22),
        axis_title_y=element_text(size=22),
        axis_text_x=element_text(size=16, rotation=45, ha="right"),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
    )
)

# Save at 300 DPI for 3600x3600 pixel output
plot.save("plot.png", dpi=300, width=12, height=12)
