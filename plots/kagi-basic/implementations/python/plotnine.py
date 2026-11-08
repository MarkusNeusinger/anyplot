""" anyplot.ai
kagi-basic: Basic Kagi Chart
Library: plotnine 0.15.8 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-08
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

# Constants
REVERSAL = 0.04  # a 4 % move against the running extreme reverses the line
SEGMENT_COLUMNS = ["x", "x_end", "y", "y_end", "trend"]  # the derived Kagi segment table

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Price ($)"  # role: close

# Data: synthetic daily closing prices, a random walk with a slight upward drift; replace this block with your
# own table, for example df = pd.read_csv("prices.csv", parse_dates=[DATE])
np.random.seed(42)
n_days = 250
returns = np.random.normal(0.0005, 0.02, n_days)
df = pd.DataFrame(
    {DATE: pd.date_range("2024-01-01", periods=n_days, freq="B"), CLOSE: 100 * np.exp(np.cumsum(returns))}
)

# Plot: reads only df and the constants above
# Kagi construction: the line extends while the price keeps its direction and turns at a shoulder (top) or a
# waist (bottom) once the price moves against the running extreme by the reversal amount
prices = df.sort_values(DATE)[CLOSE].dropna().to_numpy(dtype=float)
direction = 1 if prices[1] > prices[0] else -1
turns = [prices[0]]
extreme = prices[0]
for price in prices[1:]:
    if (price - extreme) * direction > 0:
        extreme = price
    elif abs(price - extreme) > extreme * REVERSAL:
        turns.append(extreme)
        extreme = price
        direction = -direction
turns.append(extreme)  # the last vertical line stays open at the latest extreme

# Thickness: the line turns thick (yang) where it rises above the previous shoulder and thin (yin) where it
# falls below the previous waist, so a vertical line that crosses that level is split at it. The first price
# stands in for the shoulder or waist the first line has not formed yet
is_yang = turns[1] > turns[0]
shoulder = waist = turns[0]
segments = []
for column, (start, end) in enumerate(zip(turns[:-1], turns[1:], strict=True)):
    rising = end > start
    level = shoulder if rising else waist
    if is_yang != rising and min(start, end) < level < max(start, end):
        segments.append((column, column, start, level, "yang" if is_yang else "yin"))
        start, is_yang = level, rising
    trend = "yang" if is_yang else "yin"
    segments.append((column, column, start, end, trend))
    if column < len(turns) - 2:
        segments.append((column, column + 1, end, end, trend))
    if rising:
        shoulder = end
    else:
        waist = end
x, x_end, y, y_end, trend_col = SEGMENT_COLUMNS
kagi_df = pd.DataFrame(segments, columns=SEGMENT_COLUMNS)

# plotnine draws the groups in category order, so yang comes last and its thick line covers the thin line's
# round caps where the two meet
kagi_df[trend_col] = pd.Categorical(kagi_df[trend_col], categories=["yin", "yang"])

# Color and width share one scale name and labels, so plotnine draws a single legend
plot = (
    ggplot(kagi_df, aes(x=x, xend=x_end, y=y, yend=y_end, color=trend_col, size=trend_col))
    + geom_segment(lineend="round")
    + scale_color_manual(name="Trend", values=TREND_COLORS, labels=TREND_LABELS, limits=list(TREND_COLORS))
    + scale_size_manual(name="Trend", values=TREND_WIDTHS, labels=TREND_LABELS, limits=list(TREND_COLORS))
    + labs(x="Kagi Line Index", y=CLOSE, title="kagi-basic · python · plotnine · anyplot.ai")
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
        legend_margin=8,
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        plot_margin_right=0.03,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
