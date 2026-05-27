""" anyplot.ai
line-navigator: Line Chart with Mini Navigator
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-27
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_rect,
    geom_vline,
    ggplot,
    labs,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # anyplot palette position 1 — ALWAYS first series

# Data - 3 years of daily temperature sensor readings (1100 data points)
np.random.seed(42)
n_days = 1100
dates = pd.date_range("2021-01-01", periods=n_days, freq="D")

day_of_year = np.arange(n_days) % 365
seasonal = 20 * np.sin(2 * np.pi * day_of_year / 365)
trend = np.linspace(0, 8, n_days)
noise = np.random.normal(0, 3, n_days)
anomalies = np.zeros(n_days)
for idx in [150, 420, 680, 950]:
    if idx < n_days:
        anomalies[idx : idx + 5] = np.random.uniform(8, 15, min(5, n_days - idx))

value = 50 + seasonal + trend + noise + anomalies
df = pd.DataFrame({"date": dates, "value": value})

# Selected range for detail view (~4 months)
range_start = pd.Timestamp("2022-06-01")
range_end = pd.Timestamp("2022-10-15")
df_detail = df[(df["date"] >= range_start) & (df["date"] <= range_end)].copy()
range_highlight = pd.DataFrame({"xmin": [range_start], "xmax": [range_end]})
nav_y_min = df["value"].min()
nav_y_max = df["value"].max()

# Title (47 chars < 67 baseline → ratio = 1.0, fontsize = 12pt)
title_str = "line-navigator · python · plotnine · anyplot.ai"

# Shared anyplot theme (theme-adaptive chrome)
shared_theme = theme_minimal() + theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    plot_title=element_text(color=INK, size=12),
    legend_text=element_text(color=INK_SOFT, size=8),
    text=element_text(color=INK),
)

# Detail view - main chart showing selected range in full resolution
p_detail = (
    ggplot(df_detail, aes(x="date", y="value"))
    + geom_line(color=BRAND, size=1.0)
    + scale_x_datetime(date_labels="%d %b", date_breaks="2 weeks")
    + scale_y_continuous(labels=lambda x: [f"{v:.0f}°C" for v in x])
    + labs(x="", y="Temperature (°C)", title=title_str)
    + shared_theme
    + theme(axis_text_x=element_text(angle=45, ha="right", color=INK_SOFT))
)

# Navigator - mini chart with full data extent and selection highlight
p_navigator = (
    ggplot(df, aes(x="date", y="value"))
    + geom_rect(
        data=range_highlight,
        mapping=aes(xmin="xmin", xmax="xmax"),
        ymin=-np.inf,
        ymax=np.inf,
        fill=BRAND,
        alpha=0.2,
        inherit_aes=False,
    )
    + geom_vline(data=range_highlight, mapping=aes(xintercept="xmin"), color=BRAND, size=1.2, linetype="solid")
    + geom_vline(data=range_highlight, mapping=aes(xintercept="xmax"), color=BRAND, size=1.2, linetype="solid")
    + geom_line(color=BRAND, size=0.5, alpha=0.7)
    + annotate(
        "text",
        x=range_start + (range_end - range_start) / 2,
        y=nav_y_max - (nav_y_max - nav_y_min) * 0.12,
        label="Selected",
        size=2.5,
        color=INK_SOFT,
    )
    + scale_x_datetime(date_labels="%Y", date_breaks="1 year")
    + scale_y_continuous(breaks=[30, 50, 70, 90], labels=lambda x: [f"{v:.0f}" for v in x])
    + labs(x="Date", y="", title="Overview")
    + shared_theme
    + theme(
        plot_title=element_text(size=8, color=INK_SOFT),
        axis_text=element_text(size=7, color=INK_SOFT),
        axis_title=element_text(size=8, color=INK_SOFT),
        panel_grid_major=element_blank(),
    )
)

# Compose: detail on top, navigator below
grid = p_detail / p_navigator
fig = grid.draw()

# Canvas: exactly 8 × 4.5 in @ 400 dpi = 3200 × 1800 px
fig.set_size_inches(8, 4.5)
fig.patch.set_facecolor(PAGE_BG)

# Set panel heights: main chart ~82%, navigator ~18% of content area
axes = fig.axes
if len(axes) >= 2:
    left = axes[0].get_position().x0
    width = axes[0].get_position().width
    bottom_margin = 0.12
    top_margin = 0.06
    gap = 0.04
    available = 1.0 - bottom_margin - top_margin - gap
    nav_ratio = 0.155  # nav_h / main_h ≈ 18%
    nav_h = available * nav_ratio
    main_h = available * (1 - nav_ratio)
    axes[1].set_position([left, bottom_margin, width, nav_h])
    axes[0].set_position([left, bottom_margin + nav_h + gap, width, main_h])

# Save (no bbox_inches='tight' — preserves exact 3200 × 1800)
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
