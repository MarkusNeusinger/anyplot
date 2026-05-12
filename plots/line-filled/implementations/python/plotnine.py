""" anyplot.ai
line-filled: Filled Line Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_area,
    geom_line,
    ggplot,
    labs,
    scale_x_continuous,
    theme,
    theme_minimal,
)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Monthly website traffic over a year
np.random.seed(42)
months = np.arange(1, 13)
base_traffic = 50000 + np.cumsum(np.random.randn(12) * 5000)
seasonal = 10000 * np.sin(np.pi * months / 6)
visitors = base_traffic + seasonal + np.random.randn(12) * 3000
visitors = np.maximum(visitors, 20000)

df = pd.DataFrame({"Month": months, "Visitors": visitors})

# Plot
plot = (
    ggplot(df, aes(x="Month", y="Visitors"))
    + geom_area(fill=BRAND, alpha=0.4)
    + geom_line(color=BRAND, size=2)
    + labs(
        x="Month",
        y="Website Visitors",
        title="line-filled · plotnine · anyplot.ai",
    )
    + scale_x_continuous(breaks=range(1, 13))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(alpha=0),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, color=INK),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
