""" anyplot.ai
line-basic: Basic Line Plot
Library: plotnine 0.15.3 | Python 3.13.13
Quality: 89/100 | Updated: 2026-04-29
"""

import os
import sys


# Prevent this file from shadowing the plotnine library when run from its own directory
sys.path = [p for p in sys.path if not p or os.path.abspath(p) != os.path.abspath(os.path.dirname(__file__))]

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

# Data - Monthly average temperature readings for a typical year
np.random.seed(42)
months = np.arange(1, 13)
base_temp = np.array([5, 7, 11, 15, 19, 23, 26, 25, 21, 15, 10, 6])
temperature = base_temp + np.random.randn(12) * 1.5

df = pd.DataFrame({"Month": months, "Temperature": temperature})

month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Plot
plot = (
    ggplot(df, aes(x="Month", y="Temperature"))
    + geom_line(size=2.5, color=BRAND)
    + geom_point(size=6, color=BRAND)
    + scale_x_continuous(breaks=list(range(1, 13)), labels=month_labels)
    + labs(x="Month", y="Temperature (°C)", title="line-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        text=element_text(size=14, color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3, alpha=0.15),
        panel_grid_minor=element_line(color=INK_SOFT, size=0.2, alpha=0.05),
    )
)

plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
