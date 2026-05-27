""" anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_polar,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme-adaptive colors
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette + adaptive neutral for 8 compass directions
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]
NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"
DIRECTION_COLORS = IMPRINT + [NEUTRAL]

# Data - Monsoon wind pattern (SW-dominant, distinct from westerlies)
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
frequencies = np.array([3, 5, 6, 12, 28, 35, 6, 5])

# Create DataFrame
df = pd.DataFrame(
    {"direction": pd.Categorical(directions, categories=directions, ordered=True), "frequency": frequencies}
)

# Create polar bar chart (wind rose)
plot = (
    ggplot(df, aes(x="direction", y="frequency", fill="direction"))
    + geom_bar(stat="identity", color="white", size=0.5, alpha=0.85, width=0.95)
    + coord_polar(start=-np.pi / 8)
    + scale_fill_manual(values=DIRECTION_COLORS)
    + scale_y_continuous(limits=[0, None], expand=[0, 0.5])
    + labs(title="polar-bar · letsplot · anyplot.ai", x="", y="Frequency (%)")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        plot_title=element_text(size=24, color=INK, face="bold"),
        axis_title_y=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        legend_position="none",
    )
    + ggsize(1200, 1200)
)

# Save as PNG and HTML (theme-suffixed)
ggsave(plot, f"plot-{THEME}.png", scale=3, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
