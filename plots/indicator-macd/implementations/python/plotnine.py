"""anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Created: 2026-05-16
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
    geom_col,
    geom_hline,
    geom_line,
    ggplot,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_datetime,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
MACD_COLOR = IMPRINT_PALETTE[2]  # blue
SIGNAL_COLOR = IMPRINT_PALETTE[3]  # ochre
UP_COLOR = IMPRINT_PALETTE[0]  # green: histogram above zero
DOWN_COLOR = IMPRINT_PALETTE[4]  # red: histogram below zero

# Constants
FAST_SPAN = 12  # standard MACD parameters, noted in the legend
SLOW_SPAN = 26
SIGNAL_SPAN = 9

# Columns: set these to your table's column names
DATE = "Date"  # role: date
MACD = "MACD"  # role: macd
SIGNAL = "Signal"  # role: signal
HISTOGRAM = "Histogram"  # role: histogram

# Data: replace this block with your own table, for example df = pd.read_csv("macd.csv")
rng = np.random.default_rng(42)
close = pd.Series(100 + np.cumsum(rng.standard_normal(150) * 1.5))
macd_line = close.ewm(span=FAST_SPAN, adjust=False).mean() - close.ewm(span=SLOW_SPAN, adjust=False).mean()
signal_line = macd_line.ewm(span=SIGNAL_SPAN, adjust=False).mean()
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-01", periods=len(close), freq="D"),
        MACD: macd_line,
        SIGNAL: signal_line,
        HISTOGRAM: macd_line - signal_line,
    }
)

# Plot: reads only df and the constants above
macd_label = f"{MACD} ({FAST_SPAN}, {SLOW_SPAN})"
signal_label = f"{SIGNAL} ({SIGNAL_SPAN})"
line_names = [macd_label, signal_label]

bars = df[[DATE, HISTOGRAM]].copy()
bars["Direction"] = np.where(bars[HISTOGRAM] >= 0, "Positive", "Negative")

lines = pd.concat(
    [df[[DATE]].assign(Value=df[MACD], Line=macd_label), df[[DATE]].assign(Value=df[SIGNAL], Line=signal_label)],
    ignore_index=True,
)

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.12),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_blank(),
    axis_ticks=element_blank(),
    plot_title=element_text(color=INK, size=12),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_blank(),
    legend_position=(0.02, 0.97),
)

plot = (
    ggplot()
    + geom_col(bars, aes(x=DATE, y=HISTOGRAM, fill="Direction"), width=0.8, alpha=0.75)
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.5)
    + geom_line(lines, aes(x=DATE, y="Value", color="Line"), size=0.9)
    + scale_fill_manual(values={"Positive": UP_COLOR, "Negative": DOWN_COLOR}, limits=["Positive", "Negative"])
    + scale_color_manual(values=[MACD_COLOR, SIGNAL_COLOR], limits=line_names)
    + scale_x_datetime(date_breaks="1 month", date_labels="%b %Y")
    + guides(fill="none")
    + labs(x=DATE, y=f"{MACD} value (price units)", title="indicator-macd · python · plotnine · anyplot.ai")
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
