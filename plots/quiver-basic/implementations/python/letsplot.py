""" pyplots.ai
quiver-basic: Basic Quiver Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    arrow,
    element_text,
    geom_segment,
    ggplot,
    ggsize,
    labs,
    scale_color_gradient,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - 2D rotation vector field: u = -y, v = x (circular flow pattern)
np.random.seed(42)

# Create grid (15x15 = 225 arrows for visual clarity)
grid_size = 15
x_range = np.linspace(-3, 3, grid_size)
y_range = np.linspace(-3, 3, grid_size)
X, Y = np.meshgrid(x_range, y_range)
X = X.flatten()
Y = Y.flatten()

# Vector components (rotation field: u = -y, v = x)
U = -Y
V = X

# Calculate magnitude for coloring
magnitude = np.sqrt(U**2 + V**2)

# Scale vectors for visibility (normalize and apply consistent scale)
scale_factor = 0.25
U_scaled = U / (magnitude + 0.01) * scale_factor * magnitude
V_scaled = V / (magnitude + 0.01) * scale_factor * magnitude

# Create DataFrame with segment endpoints
df = pd.DataFrame({"x": X, "y": Y, "xend": X + U_scaled, "yend": Y + V_scaled, "magnitude": magnitude})

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", xend="xend", yend="yend", color="magnitude"))
    + geom_segment(arrow=arrow(angle=20, length=8, type="closed"), size=1.2)
    + scale_color_gradient(low="#306998", high="#FFD43B", name="Magnitude")
    + labs(x="X Position", y="Y Position", title="Rotation Vector Field · quiver-basic · letsplot · pyplots.ai")
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        axis_text=element_text(size=16),
        axis_title=element_text(size=20),
        plot_title=element_text(size=24),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
    )
)

# Save PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, filename="plot.html", path=".")
