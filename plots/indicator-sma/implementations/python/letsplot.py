""" anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close"  # role: close
SMA_SHORT = "SMA 20"  # role: sma_short
SMA_MEDIUM = "SMA 50"  # role: sma_medium
SMA_LONG = "SMA 200"  # role: sma_long

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_periods = 300
returns = np.random.normal(0.0005, 0.015, n_periods)
prices = pd.Series(100 * np.cumprod(1 + returns))
df = pd.DataFrame(
    {
        DATE: pd.date_range(start="2024-01-02", periods=n_periods, freq="B"),
        CLOSE: prices,
        SMA_SHORT: prices.rolling(window=20).mean(),
        SMA_MEDIUM: prices.rolling(window=50).mean(),
        SMA_LONG: prices.rolling(window=200).mean(),
    }
)

# Plot: reads only df and the constants above
series = [CLOSE, SMA_SHORT, SMA_MEDIUM, SMA_LONG]
colors = {name: IMPRINT_PALETTE[i] for i, name in enumerate(series)}
df_long = df.melt(id_vars=[DATE], value_vars=series, var_name="Series", value_name="Price (USD)")

# Line-weight hierarchy: close thicker, SMAs thinner
df_sma = df_long[df_long["Series"] != CLOSE]
df_close = df_long[df_long["Series"] == CLOSE]

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=GRID_COLOR, size=0.5),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16),
    plot_subtitle=element_text(color=INK_SOFT, size=11),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=11),
)

plot = (
    ggplot(df_long, aes(x=DATE, y="Price (USD)", color="Series"))
    + geom_line(data=df_sma, size=1.0)
    + geom_line(data=df_close, size=1.8)
    + scale_color_manual(values=colors, breaks=series)
    + scale_x_datetime(format="%b '%y")
    + labs(
        title="indicator-sma · python · letsplot · anyplot.ai",
        subtitle="Close price (bold) vs. 20 / 50 / 200-day SMAs — watch for golden/death cross signals",
    )
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
