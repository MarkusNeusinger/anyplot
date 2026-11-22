""" anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_rect,
    element_text,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
GOLDEN_COLOR = "#DDCC77"  # Imprint amber: "golden cross" signal
DEATH_COLOR = INK_SOFT  # muted, theme-adaptive: "death cross" signal

# Constants
SMA_PERIODS = (20, 50, 200)  # standard short, medium and long windows for daily data

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Price (USD)"  # role: close
SMA_SHORT = "SMA 20"  # role: sma_short
SMA_MEDIUM = "SMA 50"  # role: sma_medium
SMA_LONG = "SMA 200"  # role: sma_long

# Data: replace this block with your own table, for example df = pd.read_csv("btc.csv", parse_dates=["Date"])
# Daily crypto close: a long range-bound accumulation phase, then an exponential-growth rally
rng = np.random.default_rng(7)
n_days = 480
dates = pd.date_range("2022-09-01", periods=n_days, freq="D")
shocks = rng.normal(0.0, 0.026, n_days)
drift = np.where(np.arange(n_days) < 260, 0.0, 0.0045)
log_dev = np.zeros(n_days)  # log distance from the starting level
for t in range(1, n_days):
    pull = 0.06 if t < 260 else 0.0  # mean reversion keeps the first phase range-bound
    log_dev[t] = (1 - pull) * log_dev[t - 1] + shocks[t] + drift[t]
close = 1600 * np.exp(log_dev)
price = pd.Series(close)
df = pd.DataFrame(
    {
        DATE: dates,
        CLOSE: close,
        # NaN until the window is full
        SMA_SHORT: price.rolling(window=SMA_PERIODS[0]).mean(),
        SMA_MEDIUM: price.rolling(window=SMA_PERIODS[1]).mean(),
        SMA_LONG: price.rolling(window=SMA_PERIODS[2]).mean(),
    }
)

# Plot: reads only df and the constants above
sma_columns = [SMA_SHORT, SMA_MEDIUM, SMA_LONG]
series_order = [CLOSE, *sma_columns]
df_long = pd.melt(df, id_vars=[DATE], value_vars=series_order, var_name="series", value_name="value")
df_long["series"] = pd.Categorical(df_long["series"], categories=series_order, ordered=True)
colors = dict(zip(series_order, IMPRINT_PALETTE, strict=False))

# Draw the SMAs first (behind) and the price on top, prominently
price_data = df_long[df_long["series"] == CLOSE]
sma_data = df_long[df_long["series"] != CLOSE].dropna(subset=["value"])

# Detect medium / long SMA crossovers (golden cross and death cross)
valid = df.dropna(subset=[SMA_MEDIUM, SMA_LONG])
gap = valid[SMA_MEDIUM] - valid[SMA_LONG]
flipped = (gap * gap.shift(1)) < 0
crossovers = valid.loc[flipped].assign(golden=gap[flipped] > 0)

plot = (
    ggplot(df_long, aes(x=DATE, y="value", color="series"))
    + geom_line(data=sma_data, size=0.7, alpha=0.9)
    + geom_line(data=price_data, size=1.0, alpha=0.95)
    + scale_color_manual(values=colors, limits=series_order)
    + scale_x_datetime(date_breaks="2 months", date_labels="%b %Y")
    + labs(x=DATE, y=CLOSE, title="indicator-sma · python · plotnine · anyplot.ai", color="")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=12, weight="bold", color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_text(size=8, rotation=30, ha="right", color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position=(0.02, 0.98),
        legend_direction="vertical",
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_major_x=element_line(alpha=0),
        panel_grid_minor=element_line(alpha=0),
    )
)

# Mark crossover signals with vertical dashed lines
for _, row in crossovers.iterrows():
    color = GOLDEN_COLOR if row["golden"] else DEATH_COLOR
    plot = plot + annotate("vline", xintercept=row[DATE], color=color, size=0.5, alpha=0.8, linetype="dashed")

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
