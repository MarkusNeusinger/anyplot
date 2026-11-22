"""anyplot.ai
indicator-rsi: RSI Technical Indicator Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-16
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
    geom_hline,
    geom_line,
    geom_rect,
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
PERIOD = 14  # standard RSI lookback
OVERBOUGHT = 70
OVERSOLD = 30
CENTERLINE = 50

# Columns: set these to your table's column names
DATE = "Date"  # role: date
RSI = "RSI (14-day)"  # role: rsi

# Data: replace this block with your own table, for example df = pd.read_csv("rsi.csv")
# Synthetic daily ETH/USD closes (a 24/7 market) with alternating trend and
# chop regimes, turned into Wilder's RSI.
rng = np.random.default_rng(2718)
n_days = 150
regime_drift = np.repeat([0.004, -0.001, -0.005, 0.0, 0.006, -0.002], 30 + PERIOD // 6)[: n_days + PERIOD]
daily_returns = regime_drift + rng.normal(0, 0.026, n_days + PERIOD)
close = pd.Series(3200 * np.exp(np.cumsum(daily_returns)))
change = close.diff()
avg_gain = change.clip(lower=0).ewm(alpha=1 / PERIOD, min_periods=PERIOD, adjust=False).mean()
avg_loss = (-change.clip(upper=0)).ewm(alpha=1 / PERIOD, min_periods=PERIOD, adjust=False).mean()
rsi = 100 - 100 / (1 + avg_gain / avg_loss)
dates = pd.date_range("2024-09-02", periods=len(close), freq="D")
df = pd.DataFrame({DATE: dates, RSI: rsi}).dropna().reset_index(drop=True)

# Plot
x_min, x_max = df[DATE].min(), df[DATE].max()
overbought = pd.DataFrame({"xmin": [x_min], "xmax": [x_max], "ymin": [OVERBOUGHT], "ymax": [100]})
oversold = pd.DataFrame({"xmin": [x_min], "xmax": [x_max], "ymin": [0], "ymax": [OVERSOLD]})
zone_colors = {"overbought": IMPRINT_PALETTE[4], "oversold": IMPRINT_PALETTE[2]}

plot = (
    ggplot(df, aes(x=DATE, y=RSI))
    # Overbought and oversold zones, lightly shaded
    + geom_rect(
        overbought,
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill=zone_colors["overbought"],
        alpha=0.16,
        inherit_aes=False,
    )
    + geom_rect(
        oversold,
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill=zone_colors["oversold"],
        alpha=0.16,
        inherit_aes=False,
    )
    # Threshold lines and centerline
    + geom_hline(yintercept=OVERBOUGHT, color=zone_colors["overbought"], size=0.7, linetype="dashed")
    + geom_hline(yintercept=OVERSOLD, color=zone_colors["oversold"], size=0.7, linetype="dashed")
    + geom_hline(yintercept=CENTERLINE, color=INK_SOFT, size=0.5, linetype="dotted", alpha=0.7)
    # RSI line in the first Imprint color
    + geom_line(color=IMPRINT_PALETTE[0], size=1.0)
    + scale_y_continuous(limits=(0, 100), breaks=range(0, 101, 10), expand=(0, 0))
    + scale_x_datetime(date_breaks="1 month", date_labels="%b %Y", expand=(0, 0))
    + labs(title="ETH/USD · indicator-rsi · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.1),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=12, weight="bold", color=INK),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
