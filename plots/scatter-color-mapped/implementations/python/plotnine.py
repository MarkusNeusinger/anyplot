"""anyplot.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-08
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    ggplot,
    guide_colorbar,
    labs,
    scale_fill_gradient,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential imprint_seq runs from position 1 to position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEQ_LOW, SEQ_HIGH = IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]

# Columns: set these to your table's column names
X_POSITION = "X Position (m)"  # role: x
Y_POSITION = "Y Position (m)"  # role: y
TEMPERATURE = "Temperature (°C)"  # role: color

# Data: temperature readings across a sensor grid; replace with e.g. df = pd.read_csv("sensors.csv")
np.random.seed(42)
n = 150
x = np.random.uniform(0, 100, n)
y = np.random.uniform(0, 100, n)
# Spatial pattern: warmer toward the upper right
temperature = 20 + 0.15 * x + 0.1 * y + np.random.normal(0, 3, n)
df = pd.DataFrame({X_POSITION: x, Y_POSITION: y, TEMPERATURE: temperature})

# Plot: reads only df and the constants above
plot = (
    ggplot(df, aes(x=X_POSITION, y=Y_POSITION, fill=TEMPERATURE))
    + geom_point(shape="o", size=3.2, stroke=0.3, color=INK, alpha=0.9)
    + scale_fill_gradient(low=SEQ_LOW, high=SEQ_HIGH, guide=guide_colorbar(nbin=100))
    + labs(title="scatter-color-mapped · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        plot_title=element_text(size=12, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        legend_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_key_height=110,
        legend_key_width=12,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
