"""anyplot.ai
area-basic: Basic Area Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-28
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
    geom_line,
    geom_ribbon,
    ggplot,
    labs,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Column names
DATE = "Date (January 2024)"  # role: x
VISITORS = "Daily Visitors (count)"  # role: y
FLOOR = "baseline"  # derived below the Data block: ymin of the filled area

# Data
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=31, freq="D")
base_traffic = 4800
trend = np.linspace(0, 2200, 31)
weekly_pattern = 1000 * np.sin(np.arange(31) * 2 * np.pi / 7)
amplitude_growth = np.linspace(1.0, 1.8, 31)
noise = np.random.normal(0, 500, 31) * amplitude_growth
visitors = base_traffic + trend + weekly_pattern * amplitude_growth + noise
visitors[14:16] -= np.array([1400, 600])
visitors[19:23] = np.mean(visitors[19:23]) * np.ones(4) + np.random.normal(0, 100, 4)
visitors = np.maximum(visitors, 1000)

df = pd.DataFrame({DATE: dates, VISITORS: visitors})

# Plot
title = "area-basic · python · plotnine · anyplot.ai"
n = len(title)
title_fontsize = max(8, round(12 * (67 / n if n > 67 else 1.0)))
df[FLOOR] = 0.0

plot = (
    ggplot(df, aes(x=DATE, y=VISITORS))
    + geom_ribbon(aes(ymin=FLOOR, ymax=VISITORS), fill=BRAND, alpha=0.35)
    + geom_line(color=BRAND, size=1.5)
    + labs(title=title)
    + scale_x_datetime(date_labels="%b %d")
    + scale_y_continuous(
        labels=lambda lst: [f"{int(v):,}" for v in lst], limits=(0, df[VISITORS].max() * 1.08), expand=(0, 0)
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK_SOFT),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=title_fontsize, weight="bold", color=INK),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        plot_background=element_rect(fill=PAGE_BG, color="none"),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_major_x=element_line(color=INK, size=0.2, alpha=0.08),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.6),
        axis_ticks_major_x=element_line(color=INK_SOFT, size=0.4),
        axis_ticks_major_y=element_blank(),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT),
        plot_margin=0.04,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
