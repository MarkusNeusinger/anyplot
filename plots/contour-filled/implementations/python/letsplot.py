"""anyplot.ai
contour-filled: Filled Contour Plot
Library: letsplot | Python 3.13
Quality: pending | Created: 2025-05-11
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
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

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Topographic elevation map
np.random.seed(42)
n_points = 60

# Coordinates in km (realistic geographic scale)
x = np.linspace(0, 50, n_points)
y = np.linspace(0, 50, n_points)
X, Y = np.meshgrid(x, y)

# Elevation model in meters - multiple peaks simulating mountain ranges
# Main peak (2500m) at position (15, 20)
peak1 = 2500 * np.exp(-((X - 15) ** 2 + (Y - 20) ** 2) / 50)
# Secondary peak (1800m) at position (35, 35)
peak2 = 1800 * np.exp(-((X - 35) ** 2 + (Y - 35) ** 2) / 40)
# Valley depression (800m baseline with deeper valley)
valley = 800 - 600 * np.exp(-((X - 25) ** 2 + (Y - 10) ** 2) / 60)
# Ridge formation along diagonal
ridge = 400 * np.exp(-((X - Y) ** 2) / 100)

Z = peak1 + peak2 + valley + ridge
Z = np.maximum(Z, 100)  # Floor at 100m elevation

# Convert to long-form DataFrame for lets-plot
df = pd.DataFrame({"longitude_km": X.flatten(), "latitude_km": Y.flatten(), "elevation_m": Z.flatten()})

# Create filled contour plot with smooth color bands
plot = (
    ggplot(df, aes(x="longitude_km", y="latitude_km", z="elevation_m"))
    + geom_contourf(aes(fill="..level.."), bins=15)
    + geom_contour(color="white", size=0.4, alpha=0.5, bins=15)
    + scale_fill_viridis(name="Elevation (m)", option="plasma")
    + labs(x="Longitude (km)", y="Latitude (km)", title="contour-filled · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_text=element_text(size=14, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, f"plot-{THEME}.html", path=".")
