""" pyplots.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_point, ggplot, labs, scale_color_cmap, theme, theme_minimal


# Data - Temperature readings across a sensor grid
np.random.seed(42)
n = 150

# Sensor positions and temperature measurements
x = np.random.uniform(0, 100, n)
y = np.random.uniform(0, 100, n)
# Temperature with spatial pattern - warmer in upper right
temperature = 20 + 0.15 * x + 0.1 * y + np.random.normal(0, 3, n)

df = pd.DataFrame({"x_position": x, "y_position": y, "temperature": temperature})

# Create plot
plot = (
    ggplot(df, aes(x="x_position", y="y_position", color="temperature"))
    + geom_point(size=4, alpha=0.8)
    + scale_color_cmap(cmap_name="viridis")
    + labs(
        x="X Position (m)",
        y="Y Position (m)",
        color="Temperature (°C)",
        title="scatter-color-mapped · plotnine · pyplots.ai",
    )
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
plot.save("plot.png", dpi=300)
