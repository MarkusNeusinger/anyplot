""" pyplots.ai
quiver-basic: Basic Quiver Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from plotnine import aes, arrow, element_text, geom_segment, ggplot, labs, scale_color_gradient, theme, theme_minimal


# Data: Create a 15x15 grid for rotation flow field (u = -y, v = x)
np.random.seed(42)
grid_size = 15
x_vals = np.linspace(-3, 3, grid_size)
y_vals = np.linspace(-3, 3, grid_size)
X, Y = np.meshgrid(x_vals, y_vals)
x = X.flatten()
y = Y.flatten()

# Rotation field: u = -y, v = x (creates counter-clockwise rotation)
u = -y
v = x

# Calculate magnitude for color encoding
magnitude = np.sqrt(u**2 + v**2)

# Scale arrows for visibility (normalize while preserving direction proportionally)
scale = 0.25
u_scaled = u / (magnitude + 0.1) * scale * magnitude
v_scaled = v / (magnitude + 0.1) * scale * magnitude

# Create DataFrame with start and end points for segments
df = pd.DataFrame({"x": x, "y": y, "xend": x + u_scaled, "yend": y + v_scaled, "magnitude": magnitude})

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", xend="xend", yend="yend", color="magnitude"))
    + geom_segment(arrow=arrow(length=0.15, type="closed"), size=1.2)
    + scale_color_gradient(low="#306998", high="#FFD43B", name="Magnitude")
    + labs(x="X Position", y="Y Position", title="quiver-basic · plotnine · pyplots.ai")
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
