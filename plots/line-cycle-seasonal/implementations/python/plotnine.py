""" anyplot.ai
line-cycle-seasonal: Cycle Plot (Seasonal Subseries)
Library: plotnine 0.15.7 | Python 3.13.13
Quality: 90/100 | Created: 2026-06-15
"""

import os
import sys


# Prevent this file from shadowing the installed plotnine package
sys.path = [p for p in sys.path if p not in ("", os.path.dirname(os.path.abspath(__file__)))]

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_segment,
    geom_vline,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — theme-independent
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # always first series — subseries lines
MEAN_COLOR = IMPRINT_PALETTE[2]  # blue — mean reference lines

# Data: monthly avg temperature (°C), temperate mid-latitude city, 2000–2024
np.random.seed(42)

YEARS = np.arange(2000, 2025)
N_YEARS = len(YEARS)
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Layout constants: each month occupies GROUP_WIDTH, separated by GAP
GROUP_WIDTH = 1.0
GAP = 0.35
STEP = GROUP_WIDTH + GAP  # 1.35 units per month slot

records = []
for mi, mname in enumerate(MONTH_NAMES):
    # Northern-hemisphere seasonal baseline — cosine peak July (mi=6)
    seasonal = 13.5 + 11.5 * np.cos(np.pi * (mi - 6) / 6)
    for yi, year in enumerate(YEARS):
        temp = seasonal + 0.035 * yi + np.random.normal(0, 0.9)
        # Spread years left-to-right across GROUP_WIDTH within each month slot
        x_pos = mi * STEP + (yi / (N_YEARS - 1)) * GROUP_WIDTH
        records.append({"month": mi + 1, "month_name": mname, "year": year, "temp": temp, "x_pos": x_pos})

df = pd.DataFrame(records)

# Monthly mean reference segments
mean_rows = []
for mi in range(12):
    mean_val = df[df["month"] == mi + 1]["temp"].mean()
    mean_rows.append({"x_start": mi * STEP - 0.05, "x_end": mi * STEP + GROUP_WIDTH + 0.05, "mean_temp": mean_val})
mean_df = pd.DataFrame(mean_rows)

# X-axis: tick labels at the centre of each month slot
x_breaks = [mi * STEP + GROUP_WIDTH / 2 for mi in range(12)]

# Vertical dividers sit mid-gap between consecutive month slots
vline_x = [mi * STEP - GAP / 2 for mi in range(1, 12)]

# Title with length-aware fontsize scaling
TITLE = "line-cycle-seasonal · python · plotnine · anyplot.ai"
n_chars = len(TITLE)
title_size = max(8, round(12 * (67 / n_chars if n_chars > 67 else 1.0)))

# Theme
anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.12),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_line_x=element_line(color=INK_SOFT, size=0.5),
    axis_line_y=element_line(color=INK_SOFT, size=0.5),
    axis_ticks=element_blank(),
    axis_title_x=element_blank(),
    axis_title_y=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    plot_title=element_text(color=INK, size=title_size),
    legend_position="none",
)

# Plot
plot = (
    ggplot(df, aes(x="x_pos", y="temp"))
    # Subtle vertical dividers between month groups
    + geom_vline(xintercept=vline_x, color=INK_SOFT, size=0.3, alpha=0.35)
    # Within-month chronological subseries lines (one line per month, years left→right)
    + geom_line(aes(group="month"), color=BRAND, size=0.6, alpha=0.8)
    # Horizontal mean reference lines — the primary seasonal comparison signal
    + geom_segment(
        data=mean_df,
        mapping=aes(x="x_start", xend="x_end", y="mean_temp", yend="mean_temp"),
        color=MEAN_COLOR,
        size=1.8,
        alpha=0.9,
    )
    + scale_x_continuous(breaks=x_breaks, labels=MONTH_NAMES, expand=(0.01, 0))
    + scale_y_continuous(expand=(0.05, 0))
    + labs(y="Avg Temperature (°C)", title=TITLE)
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
