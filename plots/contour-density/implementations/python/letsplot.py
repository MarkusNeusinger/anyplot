""" pyplots.ai
contour-density: Density Contour Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - two clusters with different spreads for bivariate distribution
np.random.seed(42)

# Cluster 1: Dense core cluster (temperature measurements)
n1 = 400
x1 = np.random.normal(loc=22, scale=3, size=n1)
y1 = np.random.normal(loc=55, scale=8, size=n1)

# Cluster 2: More diffuse cluster
n2 = 300
x2 = np.random.normal(loc=32, scale=5, size=n2)
y2 = np.random.normal(loc=75, scale=10, size=n2)

# Cluster 3: Small dense cluster
n3 = 150
x3 = np.random.normal(loc=15, scale=2, size=n3)
y3 = np.random.normal(loc=80, scale=5, size=n3)

# Combine clusters
x = np.concatenate([x1, x2, x3])
y = np.concatenate([y1, y2, y3])

df = pd.DataFrame({"temperature": x, "humidity": y})

# Plot - density contour with scatter overlay for context
plot = (
    ggplot(df, aes(x="temperature", y="humidity"))
    + geom_density2d(color="#306998", size=1.2, bins=10)
    + geom_point(color="#FFD43B", alpha=0.3, size=2)
    + labs(x="Temperature (°C)", y="Relative Humidity (%)", title="contour-density · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid=element_line(color="#888888", size=0.3),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive version
ggsave(plot, "plot.html", path=".")
