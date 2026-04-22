""" pyplots.ai
contour-filled: Filled Contour Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_tile, ggplot, labs, scale_fill_cmap, theme, theme_minimal


# Data - Mathematical function on a meshgrid (100x100 for smooth color transitions)
np.random.seed(42)
x = np.linspace(-3, 3, 100)
y = np.linspace(-3, 3, 100)
X, Y = np.meshgrid(x, y)

# Create a 2D function with multiple features (peaks and valleys)
Z = (
    np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))  # Main peak at (1, 1)
    + 0.8 * np.exp(-((X + 1.2) ** 2 + (Y + 1) ** 2))  # Secondary peak at (-1.2, -1)
    - 0.4 * np.exp(-((X + 0.5) ** 2 + (Y - 1.5) ** 2) / 0.3)  # Valley/dip
    + 0.5 * np.exp(-((X - 1.5) ** 2 + (Y + 1.5) ** 2) / 0.5)  # Third peak
)

# Convert to long-format DataFrame for plotnine
df = pd.DataFrame({"x": X.ravel(), "y": Y.ravel(), "z": Z.ravel()})

# Create filled contour visualization using geom_tile (plotnine's approach for 2D scalar fields)
plot = (
    ggplot(df, aes(x="x", y="y", fill="z"))
    + geom_tile()
    + scale_fill_cmap(cmap_name="viridis", name="Value")
    + labs(x="X Coordinate", y="Y Coordinate", title="contour-filled · plotnine · pyplots.ai")
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

# Draw the plot to access matplotlib figure for adding contour lines
fig = plot.draw()
ax = fig.axes[0]

# Add contour lines on top of the filled visualization for precise level identification
contour = ax.contour(X, Y, Z, levels=15, colors="white", linewidths=0.8, alpha=0.7)
ax.clabel(contour, inline=True, fontsize=10, fmt="%.1f")

# Save
fig.savefig("plot.png", dpi=300, bbox_inches="tight")
plt.close(fig)
