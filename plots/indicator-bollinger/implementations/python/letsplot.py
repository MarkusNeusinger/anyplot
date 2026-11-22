"""anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_ribbon,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 for the price, position 3 for the band family
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WINDOW = 20  # standard Bollinger period
NUM_STD = 2  # standard band width in standard deviations

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price"  # role: close
SMA = "20-day SMA"  # role: sma
UPPER = "Upper band (+2σ)"  # role: upper_band
LOWER = "Lower band (−2σ)"  # role: lower_band

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_periods = 120
dates = pd.date_range(start="2024-01-01", periods=n_periods, freq="B")
returns = np.random.normal(0.0005, 0.018, n_periods)
# Volatility clustering: a turbulent stretch in the middle
volatility_multiplier = np.where((np.arange(n_periods) > 40) & (np.arange(n_periods) < 70), 1.8, 1.0)
returns = returns * volatility_multiplier
close = 100 * np.exp(np.cumsum(returns))
sma = pd.Series(close).rolling(window=WINDOW).mean().values
std = pd.Series(close).rolling(window=WINDOW).std().values
df = pd.DataFrame(
    {DATE: dates, CLOSE: close, SMA: sma, UPPER: sma + NUM_STD * std, LOWER: sma - NUM_STD * std}
).dropna()

# Plot: reads only df and the constants above
series = [CLOSE, SMA, UPPER, LOWER]
long_df = df.melt(id_vars=DATE, value_vars=series, var_name="Series", value_name="Price (USD)")
colors = {CLOSE: IMPRINT_PALETTE[0], SMA: IMPRINT_PALETTE[2], UPPER: IMPRINT_PALETTE[2], LOWER: IMPRINT_PALETTE[2]}
linetypes = {CLOSE: "solid", SMA: "dashed", UPPER: "solid", LOWER: "solid"}

plot = (
    ggplot()
    + geom_ribbon(aes(x=DATE, ymin=LOWER, ymax=UPPER), data=df, fill=IMPRINT_PALETTE[2], alpha=0.2)
    + geom_line(aes(x=DATE, y="Price (USD)", color="Series", linetype="Series"), data=long_df, size=1.2)
    + scale_color_manual(values=[colors[s] for s in series], breaks=series)
    + scale_linetype_manual(values=[linetypes[s] for s in series], breaks=series)
    + labs(title="indicator-bollinger · python · letsplot · anyplot.ai", x=DATE, y="Price (USD)", color="", linetype="")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.15),
        panel_grid_minor=element_line(color=INK, size=0.1),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(color=INK),
        legend_position="top",
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
