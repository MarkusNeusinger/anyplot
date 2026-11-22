"""anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_ribbon,
    ggplot,
    labs,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: the price takes position 1, the bands position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WINDOW = 20  # periods in the moving average
NUM_STD = 2  # standard deviations between the middle band and each outer band

# Columns: set these to your table's column names
DATE = "Time (UTC)"  # role: date
CLOSE = "Close (USD)"  # role: close
SMA = "20-hour SMA (USD)"  # role: sma
UPPER = "Upper band (USD)"  # role: upper_band
LOWER = "Lower band (USD)"  # role: lower_band

# Data: replace this block with your own table, for example df = pd.read_csv("btc_hourly.csv")
# Bitcoin hourly closes: a calm stretch, one sharp overnight gap down, then a choppy regime
rng = np.random.default_rng(7)
n_hours = 168
steps = rng.normal(0.0002, 0.0035, n_hours)
steps[100:] = rng.normal(-0.0002, 0.0085, n_hours - 100)
steps[100] = -0.055
close = 64000 * np.exp(np.cumsum(steps))
rolling = pd.Series(close).rolling(WINDOW)
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-03-04 00:00", periods=n_hours, freq="h"),
        CLOSE: close,
        SMA: rolling.mean(),
        UPPER: rolling.mean() + NUM_STD * rolling.std(),
        LOWER: rolling.mean() - NUM_STD * rolling.std(),
    }
)

# Plot
bands = df.dropna(subset=[SMA, UPPER, LOWER])
band_color = IMPRINT_PALETTE[2]
title = "indicator-bollinger · python · plotnine · anyplot.ai"

plot = (
    ggplot(bands, aes(x=DATE))
    + geom_ribbon(aes(ymin=LOWER, ymax=UPPER), fill=band_color, alpha=0.18)
    + geom_line(aes(y=UPPER), color=band_color, size=0.6, linetype="dashed")
    + geom_line(aes(y=LOWER), color=band_color, size=0.6, linetype="dashed")
    + geom_line(aes(y=SMA), color=band_color, size=0.8, linetype="dotted")
    + geom_line(aes(y=CLOSE), color=IMPRINT_PALETTE[0], size=1.0)
    + scale_x_datetime(date_labels="%b %d", date_breaks="1 day")
    + labs(x=DATE, y="Price (USD)", title=title, subtitle=f"{WINDOW}-period SMA with ±{NUM_STD}σ bands")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_text(angle=45, ha="right"),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        plot_subtitle=element_text(size=9, color=INK_SOFT),
        text=element_text(size=7, color=INK),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
