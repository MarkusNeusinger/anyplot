"""anyplot.ai
contour-filled: Filled Contour Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-11
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_contour,
    geom_contourf,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_gradient,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential colormap (imprint_seq) runs from brand green to blue
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEQ_LOW, SEQ_HIGH = IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]

# Columns: set these to your table's column names
LONGITUDE = "Longitude (km)"  # role: x
LATITUDE = "Latitude (km)"  # role: y
ELEVATION = "Elevation (m)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("terrain.csv")
# Topographic elevation map on a 60 x 60 grid, in km and meters
n_points = 60
x = np.linspace(0, 50, n_points)
y = np.linspace(0, 50, n_points)
X, Y = np.meshgrid(x, y)

# Main peak (2500 m), secondary peak (1800 m), valley depression, diagonal ridge
peak1 = 2500 * np.exp(-((X - 15) ** 2 + (Y - 20) ** 2) / 50)
peak2 = 1800 * np.exp(-((X - 35) ** 2 + (Y - 35) ** 2) / 40)
valley = 800 - 600 * np.exp(-((X - 25) ** 2 + (Y - 10) ** 2) / 60)
ridge = 400 * np.exp(-((X - Y) ** 2) / 100)
Z = np.maximum(peak1 + peak2 + valley + ridge, 100)  # floor at 100 m

df = pd.DataFrame({LONGITUDE: X.flatten(), LATITUDE: Y.flatten(), ELEVATION: Z.flatten()})

# Plot
plot = (
    ggplot(df.dropna(), aes(x=LONGITUDE, y=LATITUDE, z=ELEVATION))
    + geom_contourf(aes(fill="..level.."), bins=15)
    + geom_contour(color="white", size=0.3, alpha=0.5, bins=15)
    + scale_fill_gradient(low=SEQ_LOW, high=SEQ_HIGH, name=ELEVATION)
    + labs(x=LONGITUDE, y=LATITUDE, title="contour-filled · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid=element_blank(),
        axis_ticks=element_line(color=INK_SOFT),
        axis_title=element_text(size=14, color=INK),
        axis_text=element_text(size=12, color=INK_SOFT),
        plot_title=element_text(size=18, color=INK),
        legend_text=element_text(size=12, color=INK_SOFT),
        legend_title=element_text(size=14, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
    + ggsize(800, 450)
)

# Save PNG (scale=4 gives 3200x1800) and interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
