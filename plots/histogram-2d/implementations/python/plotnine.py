""" pyplots.ai
histogram-2d: 2D Histogram Heatmap
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_bin2d, ggplot, labs, scale_fill_continuous, theme, theme_minimal


# Data - Bivariate normal distribution with correlation
np.random.seed(42)
n_points = 5000
mean = [0, 0]
# Correlation of 0.6 between x and y
cov = [[1.0, 0.6], [0.6, 1.0]]
xy = np.random.multivariate_normal(mean, cov, n_points)
df = pd.DataFrame({"x": xy[:, 0], "y": xy[:, 1]})

# Create 2D histogram heatmap
plot = (
    ggplot(df, aes(x="x", y="y"))
    + geom_bin2d(bins=40)
    + scale_fill_continuous(cmap_name="viridis", name="Count")
    + labs(x="X Value", y="Y Value", title="histogram-2d · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
