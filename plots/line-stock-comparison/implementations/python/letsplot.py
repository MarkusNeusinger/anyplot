"""anyplot.ai
line-stock-comparison: Stock Price Comparison Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-11-26
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
    geom_hline,
    geom_line,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
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
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BASE = 100  # every series is rebased to this value on the first date

# Columns: set these to your table's column names
DATE = "Date"  # role: date
SYMBOL = "Symbol"  # role: symbol
PRICE = "Price (USD)"  # role: price
REBASED = "Performance (rebased to 100)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=252, freq="B")
params = {"AAPL": (0.0008, 0.018), "GOOGL": (0.0006, 0.020), "MSFT": (0.0009, 0.016), "SPY": (0.0005, 0.010)}
frames = []
for symbol, (drift, volatility) in params.items():
    returns = np.random.normal(drift, volatility, len(dates))
    frames.append(pd.DataFrame({DATE: dates, SYMBOL: symbol, PRICE: 100 * np.exp(np.cumsum(returns))}))
df = pd.concat(frames, ignore_index=True)

# Plot
df[REBASED] = df.groupby(SYMBOL, sort=False)[PRICE].transform(lambda x: x / x.iloc[0] * BASE)

plot = (
    ggplot(df, aes(x=DATE, y=REBASED, color=SYMBOL))
    + geom_hline(yintercept=BASE, linetype="dashed", color=INK_SOFT, size=0.6, alpha=0.6)
    + geom_line(
        size=1.5, alpha=0.9, tooltips=layer_tooltips().format("^y", ".1f").line(f"@{{{SYMBOL}}}").line("Rebased|^y")
    )
    + scale_color_manual(values=IMPRINT_PALETTE)
    + labs(title="line-stock-comparison · python · letsplot · anyplot.ai", x=DATE, y=REBASED, color=SYMBOL)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=RULE, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
