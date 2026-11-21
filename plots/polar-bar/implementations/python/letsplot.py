""" anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_polar,
    element_blank,
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

# Imprint palette, one color per compass direction
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns
DIRECTION = "direction"  # role: direction
FREQUENCY = "frequency"  # role: frequency

# Data - Monsoon wind pattern (SW-dominant, distinct from westerlies)
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
df = pd.DataFrame(
    {DIRECTION: pd.Categorical(directions, categories=directions, ordered=True), FREQUENCY: [3, 5, 6, 12, 28, 35, 6, 5]}
)

# Plot
plot = (
    ggplot(df, aes(x=DIRECTION, y=FREQUENCY, fill=DIRECTION))
    + geom_bar(stat="identity", color=PAGE_BG, size=0.5, alpha=0.9, width=0.95)
    + coord_polar(start=-np.pi / df[DIRECTION].nunique())
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + scale_y_continuous(limits=[0, None], expand=[0, 0.5])
    + labs(title="polar-bar · python · letsplot · anyplot.ai", x="", y="Frequency (%)")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=16, color=INK, face="bold"),
        axis_title_y=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        legend_position="none",
    )
    + ggsize(600, 600)
)

# Save as PNG and HTML (theme-suffixed)
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
