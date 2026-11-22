"""anyplot.ai
indicator-rsi: RSI Technical Indicator Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
"""
# ruff: noqa: F405

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the RSI line, red and blue mark the two zones
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
OVERBOUGHT = 70  # RSI above this level counts as overbought
OVERSOLD = 30  # RSI below this level counts as oversold
CENTERLINE = 50  # bullish / bearish bias
LOOKBACK = 14  # standard RSI lookback in periods

# Columns: set these to your table's column names
DATE = "Date"  # role: date
RSI = "RSI (14-period)"  # role: rsi

# Data: replace this block with your own table, for example df = pd.read_csv("rsi.csv")
np.random.seed(42)
n_days = 120
dates = pd.date_range("2024-06-01", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.025, n_days)
price = 150 * np.exp(np.cumsum(returns))

delta = np.diff(price)
gains = np.where(delta > 0, delta, 0)
losses = np.where(delta < 0, -delta, 0)
avg_gain = np.zeros(len(delta))
avg_loss = np.zeros(len(delta))
avg_gain[LOOKBACK - 1] = np.mean(gains[:LOOKBACK])
avg_loss[LOOKBACK - 1] = np.mean(losses[:LOOKBACK])
for i in range(LOOKBACK, len(delta)):
    avg_gain[i] = (avg_gain[i - 1] * (LOOKBACK - 1) + gains[i]) / LOOKBACK
    avg_loss[i] = (avg_loss[i - 1] * (LOOKBACK - 1) + losses[i]) / LOOKBACK
rs = np.where(avg_loss != 0, avg_gain / avg_loss, 100)
rsi_all = 100 - (100 / (1 + rs))

rsi_values = np.full(n_days, np.nan)
rsi_values[LOOKBACK:] = rsi_all[LOOKBACK - 1 :]
df = pd.DataFrame({DATE: dates, RSI: rsi_values}).dropna()

# Plot: reads only df and the constants above
x_min, x_max = df[DATE].min(), df[DATE].max()
zones = pd.DataFrame(
    {
        "xmin": [x_min, x_min],
        "xmax": [x_max, x_max],
        "ymin": [OVERBOUGHT, 0],
        "ymax": [100, OVERSOLD],
        "zone": ["Overbought", "Oversold"],
    }
)

plot = (
    ggplot()
    + geom_rect(
        data=zones,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="zone"),
        alpha=0.14,
        size=0,
        show_legend=False,
    )
    + scale_fill_manual(values={"Overbought": IMPRINT_PALETTE[4], "Oversold": IMPRINT_PALETTE[2]})
    + geom_hline(yintercept=OVERBOUGHT, color=IMPRINT_PALETTE[4], size=0.8, linetype="dashed")
    + geom_hline(yintercept=OVERSOLD, color=IMPRINT_PALETTE[2], size=0.8, linetype="dashed")
    + geom_hline(yintercept=CENTERLINE, color=INK_SOFT, size=0.5, linetype="dotted")
    + geom_line(data=df, mapping=aes(x=DATE, y=RSI), color=IMPRINT_PALETTE[0], size=1.4)
    + labs(title="indicator-rsi · python · letsplot · anyplot.ai", x=DATE, y=RSI)
    + scale_y_continuous(limits=[0, 100], breaks=[0, OVERSOLD, CENTERLINE, OVERBOUGHT, 100])
    + scale_x_datetime(format="%b %Y")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.2),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
