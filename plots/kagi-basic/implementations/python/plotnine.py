""" anyplot.ai
kagi-basic: Basic Kagi Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
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
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_size_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint semantic anchors: green for yang (bullish), red for yin (bearish)
TREND_COLORS = {"yang": "#009E73", "yin": "#AE3030"}
TREND_WIDTHS = {"yang": 1.5, "yin": 0.5}
TREND_LABELS = {"yang": "Yang (bullish)", "yin": "Yin (bearish)"}
REVERSAL = 0.04  # a 4 % move against the running extreme reverses the line

# Data: synthetic daily closing prices, a random walk with a slight upward drift
np.random.seed(42)
n_days = 250
returns = np.random.normal(0.0005, 0.02, n_days)
df_prices = pd.DataFrame(
    {"date": pd.date_range("2024-01-01", periods=n_days, freq="B"), "close": 100 * np.exp(np.cumsum(returns))}
)

# Kagi construction: each reversal adds a vertical line and the shoulder or waist that joins it to the next column
prices = df_prices["close"].to_numpy()
direction = 1 if prices[1] > prices[0] else -1
high = low = segment_start = prices[0]
is_yang = direction == 1
column = 0
segments = []
for price in prices[1:]:
    if direction == 1:
        if price > high:
            high = price
            is_yang = True
        elif price < high * (1 - REVERSAL):
            trend = "yang" if is_yang else "yin"
            segments += [(column, column, segment_start, high, trend), (column, column + 1, high, high, trend)]
            column += 1
            direction = -1
            segment_start = high
            high = low = price
    else:
        if price < low:
            low = price
            is_yang = False
        elif price > low * (1 + REVERSAL):
            trend = "yang" if is_yang else "yin"
            segments += [(column, column, segment_start, low, trend), (column, column + 1, low, low, trend)]
            column += 1
            direction = 1
            segment_start = low
            high = low = price

# The last vertical line stays open at the latest extreme
last_end = max(high, prices[-1]) if direction == 1 else min(low, prices[-1])
segments.append((column, column, segment_start, last_end, "yang" if is_yang else "yin"))
kagi_df = pd.DataFrame(segments, columns=["x", "x_end", "y", "y_end", "trend"])

# Plot: plotnine draws the groups in category order, so yang comes last and its thick line covers the
# thin line's round caps where the two meet
kagi_df["trend"] = pd.Categorical(kagi_df["trend"], categories=["yin", "yang"])

# Color and width share one scale name and labels, so plotnine draws a single legend
plot = (
    ggplot(kagi_df, aes(x="x", xend="x_end", y="y", yend="y_end", color="trend", size="trend"))
    + geom_segment(lineend="round")
    + scale_color_manual(name="Trend", values=TREND_COLORS, labels=TREND_LABELS, limits=list(TREND_COLORS))
    + scale_size_manual(name="Trend", values=TREND_WIDTHS, labels=TREND_LABELS, limits=list(TREND_COLORS))
    + labs(x="Kagi Line Index", y="Price ($)", title="kagi-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        plot_title=element_text(size=12, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        axis_ticks=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.12),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        plot_margin_right=0.03,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
