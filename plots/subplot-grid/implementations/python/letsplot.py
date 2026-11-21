"""anyplot.ai
subplot-grid: Subplot Grid Layout
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme tokens
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MA_WINDOW = 10  # trading days in the moving average

# Columns: set these to your table's column names
DAY = "Trading Day"  # role: x
PRICE = "Price ($)"  # role: y
VOLUME = "Volume (Millions)"  # role: extra
DAILY_RETURN = "Daily Return (%)"  # role: extra
ABS_RETURN = "Absolute Return (%)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
days = 60
returns = np.random.normal(0.001, 0.02, days)
price = 100 * np.cumprod(1 + returns)
volume = 1_000_000 * (1 + 0.5 * np.abs(returns) / 0.02 + np.random.uniform(0, 0.5, days))
log_returns = np.r_[np.nan, np.diff(np.log(price)) * 100]
df = pd.DataFrame(
    {
        DAY: np.arange(days),
        PRICE: price,
        VOLUME: volume / 1_000_000,
        DAILY_RETURN: log_returns,
        ABS_RETURN: np.abs(log_returns),
    }
)

# Plot
df["Moving average"] = df[PRICE].rolling(window=MA_WINDOW, min_periods=1).mean()

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.15),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=11, color=INK),
    axis_text=element_text(size=9, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.25),
    axis_ticks=element_line(color=INK_SOFT, size=0.25),
    plot_title=element_text(size=11, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=9),
    legend_title=element_text(color=INK, size=9),
)

# Top left: price line with moving average
price_plot = (
    ggplot(df, aes(x=DAY, y=PRICE))
    + geom_line(color=IMPRINT_PALETTE[0], size=0.75)
    + geom_line(aes(y="Moving average"), color=IMPRINT_PALETTE[1], size=0.6, linetype="dashed")
    + labs(y=PRICE, title="Stock Price with 10-Day Moving Average")
    + theme_minimal()
    + anyplot_theme
)

# Top right: volume bars
volume_plot = (
    ggplot(df, aes(x=DAY, y=VOLUME))
    + geom_bar(stat="identity", fill=IMPRINT_PALETTE[2], alpha=0.8, width=0.8)
    + labs(title="Daily Trading Volume")
    + theme_minimal()
    + anyplot_theme
)

# Bottom left: returns histogram with zero reference
returns_plot = (
    ggplot(df, aes(x=DAILY_RETURN))
    + geom_histogram(fill=IMPRINT_PALETTE[3], color=INK_SOFT, bins=20, alpha=0.8, size=0.2)
    + geom_vline(xintercept=0, color=IMPRINT_PALETTE[0], size=0.75, linetype="dashed")
    + labs(y="Frequency", title="Distribution of Daily Returns")
    + theme_minimal()
    + anyplot_theme
)

# Bottom right: volume vs absolute return with linear trend
scatter_plot = (
    ggplot(df, aes(x=ABS_RETURN, y=VOLUME))
    + geom_point(color=IMPRINT_PALETTE[4], size=2, alpha=0.7)
    + geom_smooth(method="lm", color=IMPRINT_PALETTE[0], size=0.75, fill=None)
    + labs(title="Volume vs Price Movement")
    + theme_minimal()
    + anyplot_theme
)

grid_plot = gggrid([price_plot, volume_plot, returns_plot, scatter_plot], ncol=2)
final_plot = (
    grid_plot
    + ggsize(800, 450)
    + ggtitle("subplot-grid · python · letsplot · anyplot.ai")
    + theme(plot_title=element_text(size=15, color=INK), plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))
)

ggsave(final_plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(final_plot, f"plot-{THEME}.html", path=".")
