""" anyplot.ai
line-markers: Line Plot with Markers
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_shape_manual,
    theme,
    theme_minimal,
)


# Theme colors
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD"]

# Data: Monthly temperature readings from two weather stations
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Station A: Coastal location (milder temperatures)
station_a = np.array([8, 9, 12, 15, 19, 23, 26, 26, 22, 17, 12, 9]) + np.random.randn(12) * 0.5

# Station B: Inland location (more extreme temperatures)
station_b = np.array([2, 4, 10, 16, 21, 26, 29, 28, 22, 14, 7, 3]) + np.random.randn(12) * 0.5

df = pd.DataFrame(
    {
        "Month": month_labels * 2,
        "Month_Num": list(months) * 2,
        "Temperature": np.concatenate([station_a, station_b]),
        "Station": ["Coastal Station"] * 12 + ["Inland Station"] * 12,
    }
)

anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.4),
    plot_title=element_text(color=INK, size=24, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.4),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
    legend_position="right",
    text=element_text(size=14),
)

# Plot
plot = (
    ggplot(df, aes(x="Month_Num", y="Temperature", color="Station", shape="Station"))
    + geom_line(size=1.5, alpha=0.85)
    + geom_point(size=5, alpha=0.9)
    + scale_color_manual(values=IMPRINT)
    + scale_shape_manual(values=["o", "s"])
    + labs(
        x="Month",
        y="Temperature (°C)",
        title="Temperature Comparison: Coastal vs Inland Stations",
        color="Weather Station",
        shape="Weather Station",
    )
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
