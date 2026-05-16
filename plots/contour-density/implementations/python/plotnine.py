"""anyplot.ai
contour-density: Density Contour Plot
Library: plotnine | Python 3.13
Quality: pending | Created: 2025-05-16
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

# Data - create bivariate distribution with clusters
np.random.seed(42)

# Main cluster
n1 = 300
x1 = np.random.normal(50, 8, n1)
y1 = np.random.normal(45, 10, n1)

# Secondary cluster
n2 = 200
x2 = np.random.normal(75, 6, n2)
y2 = np.random.normal(70, 7, n2)

# Smaller outlying cluster
n3 = 100
x3 = np.random.normal(30, 5, n3)
y3 = np.random.normal(75, 5, n3)

# Combine all data
x = np.concatenate([x1, x2, x3])
y = np.concatenate([y1, y2, y3])

df = pd.DataFrame({"Temperature (°C)": x, "Pressure (kPa)": y})

# Plot
plot = (
    ggplot(df, aes(x="Temperature (°C)", y="Pressure (kPa)"))
    + geom_density_2d(stat=stat_density_2d(levels=12), color="#009E73", size=1.5)
    + geom_point(alpha=0.15, size=2.5, color=INK_SOFT)
    + labs(x="Temperature (°C)", y="Pressure (kPa)", title="contour-density · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
