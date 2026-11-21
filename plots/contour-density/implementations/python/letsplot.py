"""anyplot.ai
contour-density: Density Contour Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
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

# Imprint palette: single series, position 1
BRAND = "#009E73"

# Columns: set these to your table's column names
TEMPERATURE = "Temperature (°C)"  # role: x
HUMIDITY = "Relative Humidity (%)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
rng = np.random.default_rng(42)
clusters = [
    (400, 22, 3, 55, 8),  # dense core cluster
    (300, 32, 5, 75, 10),  # more diffuse cluster
    (150, 15, 2, 80, 5),  # small dense cluster
]
df = pd.DataFrame(
    {
        TEMPERATURE: np.concatenate([rng.normal(mx, sx, n) for n, mx, sx, _, _ in clusters]),
        HUMIDITY: np.concatenate([rng.normal(my, sy, n) for n, _, _, my, sy in clusters]),
    }
)

# Plot: density contours with a faint scatter overlay for context
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=RULE, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    plot_title=element_text(size=16, color=INK),
    axis_line=element_line(color=INK_SOFT, size=0.5),
)

plot = (
    ggplot(df, aes(x=TEMPERATURE, y=HUMIDITY))
    + geom_point(color=BRAND, alpha=0.2, size=1.5)
    + geom_density2d(color=BRAND, size=0.9, bins=10)
    + labs(title="contour-density · python · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Output
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
