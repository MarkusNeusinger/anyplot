""" pyplots.ai
contour-basic: Basic Contour Plot
Library: plotnine 0.15.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-14
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_tile, ggplot, labs, scale_fill_cmap, theme, theme_minimal


# Data - Mathematical function on a meshgrid
np.random.seed(42)
x = np.linspace(-3, 3, 100)
y = np.linspace(-3, 3, 100)
X, Y = np.meshgrid(x, y)

# Create a 2D Gaussian function with two peaks
Z = (
    np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))
    + 0.7 * np.exp(-((X + 1) ** 2 + (Y + 1) ** 2))
    - 0.3 * np.exp(-((X) ** 2 + (Y - 1.5) ** 2) / 0.5)
)

# Convert to long-format DataFrame for plotnine
df = pd.DataFrame({"x": X.ravel(), "y": Y.ravel(), "z": Z.ravel()})

# Create plotnine heatmap as base for contour visualization
plot = (
    ggplot(df, aes(x="x", y="y", fill="z"))
    + geom_tile()
    + scale_fill_cmap(cmap_name="viridis", name="Value")
    + labs(x="X Coordinate", y="Y Coordinate", title="contour-basic \u00b7 plotnine \u00b7 pyplots.ai")
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

# Draw the plot to access matplotlib axes
fig = plot.draw()
ax = fig.axes[0]

# Add matplotlib contour lines on top of the plotnine heatmap
contour = ax.contour(X, Y, Z, levels=12, colors="white", linewidths=0.8, alpha=0.7)
ax.clabel(contour, inline=True, fontsize=10, fmt="%.1f")

# Save
fig.savefig("plot.png", dpi=300, bbox_inches="tight")
plt.close(fig)
