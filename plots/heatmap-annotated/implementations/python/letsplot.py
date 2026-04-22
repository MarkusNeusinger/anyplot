""" pyplots.ai
heatmap-annotated: Annotated Heatmap
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Correlation matrix for stock sectors
np.random.seed(42)
sectors = ["Tech", "Finance", "Healthcare", "Energy", "Consumer", "Industrial", "Materials", "Utilities"]
n = len(sectors)

# Generate a realistic correlation matrix
base_corr = np.random.uniform(-0.3, 0.8, (n, n))
corr_matrix = (base_corr + base_corr.T) / 2
np.fill_diagonal(corr_matrix, 1.0)
corr_matrix = np.clip(corr_matrix, -1, 1)

# Create dataframe in long format for lets-plot
rows = []
for i, row_sector in enumerate(sectors):
    for j, col_sector in enumerate(sectors):
        rows.append({"x": col_sector, "y": row_sector, "value": corr_matrix[i, j]})

df = pd.DataFrame(rows)

# Reverse y-axis order for proper matrix display
df["y"] = pd.Categorical(df["y"], categories=sectors[::-1], ordered=True)
df["x"] = pd.Categorical(df["x"], categories=sectors, ordered=True)

# Format values for annotation
df["label"] = df["value"].apply(lambda v: f"{v:.2f}")

# Determine text color based on value (dark text for light cells, light for dark)
df["text_color"] = df["value"].apply(lambda v: "white" if abs(v) > 0.5 else "black")

# Create heatmap with annotations
plot = (
    ggplot(df, aes(x="x", y="y", fill="value"))
    + geom_tile(color="white", size=0.5)
    + geom_text(aes(label="label", color="text_color"), size=12, fontface="bold")
    + scale_color_identity()
    + scale_fill_gradient2(low="#2166AC", mid="#F7F7F7", high="#B2182B", midpoint=0, name="Correlation", limits=[-1, 1])
    + labs(x="Sector", y="Sector", title="heatmap-annotated · lets-plot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=45, hjust=1),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        panel_grid=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, "plot.html", path=".")
