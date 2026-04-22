""" pyplots.ai
contour-filled: Filled Contour Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
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

# Data - Create a 2D surface with multiple features
np.random.seed(42)
n_points = 60

x = np.linspace(-4, 4, n_points)
y = np.linspace(-4, 4, n_points)
X, Y = np.meshgrid(x, y)

# Mathematical function: combination of peaks and a saddle
# Main peak at (1.5, 1.5)
peak1 = 1.0 * np.exp(-((X - 1.5) ** 2 + (Y - 1.5) ** 2) / 1.5)
# Secondary peak at (-1.5, -1.5)
peak2 = 0.7 * np.exp(-((X + 1.5) ** 2 + (Y + 1.5) ** 2) / 1.2)
# Valley/depression at (1.5, -1.5)
valley = -0.5 * np.exp(-((X - 1.5) ** 2 + (Y + 1.5) ** 2) / 1.0)
# Ridge along diagonal
ridge = 0.3 * np.exp(-((X + Y) ** 2) / 4)

Z = peak1 + peak2 + valley + ridge

# Convert to long-form DataFrame for lets-plot
df = pd.DataFrame({"x": X.flatten(), "y": Y.flatten(), "z": Z.flatten()})

# Create filled contour plot with smooth color bands
plot = (
    ggplot(df, aes(x="x", y="y", z="z"))
    + geom_contourf(aes(fill="..level.."), bins=15)
    + geom_contour(color="white", size=0.4, alpha=0.5, bins=15)
    + scale_fill_viridis(name="Value", option="plasma")
    + labs(x="X Coordinate", y="Y Coordinate", title="contour-filled \u00b7 letsplot \u00b7 pyplots.ai")
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
