""" anyplot.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-08
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_cmap,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

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
    + geom_tile(color=INK_SOFT, size=0.5)
    + geom_text(aes(label="Correlation"), format_string="{:.2f}", size=14, color=INK)
    + scale_fill_cmap(cmap_name="BrBG", limits=(-1, 1), name="Correlation\nCoefficient")
    + coord_fixed(ratio=1)
    + labs(title="heatmap-correlation · plotnine · anyplot.ai", x="Portfolio Asset", y="Portfolio Asset")
    + theme_minimal()
    + theme(
        figure_size=(12, 12),  # 12x12 at 300 DPI = 3600x3600 px
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        plot_title=element_text(size=26, color=INK, ha="center", weight="bold"),
        axis_title_x=element_text(size=22, color=INK),
        axis_title_y=element_text(size=22, color=INK),
        axis_text_x=element_text(size=16, color=INK_SOFT, rotation=45, ha="right"),
        axis_text_y=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
    )
)

# Save at 300 DPI for 3600x3600 pixel output
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
plot.save(f"plot-{THEME}.png", dpi=300, width=12, height=12)
