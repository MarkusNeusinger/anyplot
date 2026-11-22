""" anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
POSITIVE = "#009E73"  # position 1: positive histogram bars
NEGATIVE = "#AE3030"  # imprint red: negative histogram bars
MACD_COLOR = "#4467A3"  # imprint blue: MACD line
SIGNAL_COLOR = "#BD8233"  # imprint ochre: signal line

# Constants
FAST, SLOW, SIGNAL_SPAN = 12, 26, 9

# Column names
DATE = "date"  # role: date
MACD = "macd"  # role: macd
SIGNAL = "signal"  # role: signal
HISTOGRAM = "histogram"  # role: histogram

# Data
np.random.seed(42)
n_days = 120
warmup = 35
dates = pd.date_range(start="2024-01-01", periods=n_days + warmup, freq="B")
returns = np.random.normal(0.0005, 0.015, n_days + warmup)
returns = returns + np.sin(np.linspace(0, 4 * np.pi, n_days + warmup)) * 0.012
prices = pd.Series(100 * np.cumprod(1 + returns))

macd_full = prices.ewm(span=FAST, adjust=False).mean() - prices.ewm(span=SLOW, adjust=False).mean()
signal_full = macd_full.ewm(span=SIGNAL_SPAN, adjust=False).mean()
df = pd.DataFrame({DATE: dates, MACD: macd_full, SIGNAL: signal_full, HISTOGRAM: macd_full - signal_full}).iloc[warmup:]

# Plot
df = df.reset_index(drop=True)
df["day"] = np.arange(len(df))
df["direction"] = np.where(df[HISTOGRAM] >= 0, "Positive", "Negative")
df_lines = df.melt(id_vars="day", value_vars=[MACD, SIGNAL], var_name="line", value_name="value")
df_lines["line"] = df_lines["line"].map({MACD: "MACD line", SIGNAL: "Signal line"})

plot = (
    ggplot()
    + geom_bar(
        data=df,
        mapping=aes(x="day", y=HISTOGRAM, fill="direction"),
        stat="identity",
        width=0.8,
        alpha=0.8,
        color=PAGE_BG,
        size=0.2,
    )
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.5, linetype="dashed")
    + geom_line(data=df_lines, mapping=aes(x="day", y="value", color="line"), size=1.0)
    + scale_fill_manual(values={"Positive": POSITIVE, "Negative": NEGATIVE}, name="Histogram")
    + scale_color_manual(values={"MACD line": MACD_COLOR, "Signal line": SIGNAL_COLOR}, name="Lines")
    + labs(
        x="Trading Day",
        y="MACD value",
        title="indicator-macd · python · letsplot · anyplot.ai",
        subtitle=f"MACD parameters: fast EMA {FAST}, slow EMA {SLOW}, signal EMA {SIGNAL_SPAN}",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.2),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        plot_subtitle=element_text(size=12, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
