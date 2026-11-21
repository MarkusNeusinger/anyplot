"""anyplot.ai
contour-density: Density Contour Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_density_2d,
    geom_point,
    ggplot,
    labs,
    stat_density_2d,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Constants
TEMPERATURE = "Temperature (°C)"  # role: x
PRESSURE = "Pressure (kPa)"  # role: y

# Data - bivariate distribution with three clusters
np.random.seed(42)
x1 = np.random.normal(50, 8, 300)
y1 = np.random.normal(45, 10, 300)
x2 = np.random.normal(75, 6, 200)
y2 = np.random.normal(70, 7, 200)
x3 = np.random.normal(30, 5, 100)
y3 = np.random.normal(75, 5, 100)

df = pd.DataFrame({TEMPERATURE: np.concatenate([x1, x2, x3]), PRESSURE: np.concatenate([y1, y2, y3])})

# Plot
plot = (
    ggplot(df, aes(x=TEMPERATURE, y=PRESSURE))
    + geom_density_2d(stat=stat_density_2d(levels=12), color="#009E73", size=0.8)
    + geom_point(alpha=0.15, size=1.5, color=INK_SOFT)
    + labs(title="contour-density · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.15, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.1, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
