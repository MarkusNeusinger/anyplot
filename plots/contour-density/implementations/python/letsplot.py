"""anyplot.ai
contour-density: Density Contour Plot
Library: letsplot | Python 3.13
Quality: 92/100 | Created: 2025-12-30
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data - three clusters with different spreads for bivariate distribution
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
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=RULE, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    plot_title=element_text(size=24, color=INK),
    axis_line=element_line(color=INK_SOFT, size=0.5),
)

plot = (
    ggplot(df, aes(x="temperature", y="humidity"))
    + geom_density2d(color=BRAND, size=1.2, bins=10)
    + geom_point(color=BRAND, alpha=0.2, size=2)
    + labs(x="Temperature (°C)", y="Relative Humidity (%)", title="contour-density · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", scale=3, path=".")

# Save as HTML for interactive version
ggsave(plot, f"plot-{THEME}.html", path=".")
