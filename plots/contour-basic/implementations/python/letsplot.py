""" pyplots.ai
contour-basic: Basic Contour Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_contour,
    geom_contourf,
    ggplot,
    ggsize,
    labs,
    scale_fill_viridis,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Create a 2D Gaussian surface
np.random.seed(42)
n_points = 50

x = np.linspace(-3, 3, n_points)
y = np.linspace(-3, 3, n_points)
X, Y = np.meshgrid(x, y)

# Mathematical function: sum of two Gaussian peaks
Z = np.exp(-((X - 1) ** 2 + (Y - 1) ** 2)) + 0.7 * np.exp(-((X + 1) ** 2 + (Y + 1) ** 2))

# Convert to long-form DataFrame for lets-plot
df = pd.DataFrame({"x": X.flatten(), "y": Y.flatten(), "z": Z.flatten()})

# Create contour plot with filled regions and contour lines
plot = (
    ggplot(df, aes(x="x", y="y", z="z"))
    + geom_contourf(aes(fill="..level.."), bins=12)
    + geom_contour(color="white", size=0.5, alpha=0.6, bins=12)
    + scale_fill_viridis(name="Value")
    + labs(x="X Coordinate", y="Y Coordinate", title="contour-basic · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, "plot.html", path=".")
