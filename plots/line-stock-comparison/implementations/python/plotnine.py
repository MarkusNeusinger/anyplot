"""anyplot.ai
line-stock-comparison: Stock Price Comparison Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-26
"""

import os
import sys


_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if not p or os.path.abspath(p) != _script_dir]

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
    geom_point,
    geom_ribbon,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_date,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BASE = 100  # every series is rebased to this value on its first date
BENCHMARK = "SPY"  # the index the stocks are compared against, drawn heavier

# Columns: set these to your table's column names
DATE = "Date"  # role: date
SYMBOL = "Symbol"  # role: symbol
PRICE = "Price (USD)"  # role: price

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 252
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")
params = {"AAPL": (0.0005, 0.013), "GOOGL": (0.0003, 0.015), "MSFT": (0.0006, 0.012), "SPY": (0.0004, 0.008)}

frames = []
for symbol, (drift, vol) in params.items():
    daily_returns = np.random.normal(drift, vol, n_days)
    frames.append(pd.DataFrame({DATE: dates, SYMBOL: symbol, PRICE: 100 * np.exp(np.cumsum(daily_returns))}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
REBASED = "Rebased price (start = 100)"
groups = df[SYMBOL].unique().tolist()
df = df.sort_values([SYMBOL, DATE])
df[REBASED] = df[PRICE] / df.groupby(SYMBOL, sort=False)[PRICE].transform("first") * BASE

bench_df = df[df[SYMBOL] == BENCHMARK]
others_df = df[df[SYMBOL] != BENCHMARK]

# End-of-line markers and value labels, one per series
LABEL, LABEL_DATE = "label", "label_date"
last_df = df.groupby(SYMBOL, sort=False).tail(1).copy()
last_df[LABEL] = last_df[SYMBOL] + " " + last_df[REBASED].map(lambda v: f"{v:.0f}")
last_df[LABEL_DATE] = last_df[DATE] + pd.Timedelta(days=7)

# Benchmark outperformance ribbon: shades the region where the benchmark stands above the base
YMIN, YMAX = "ymin", "ymax"
ribbon_df = bench_df.loc[bench_df[REBASED] > BASE, [DATE, REBASED]].rename(columns={REBASED: YMAX})
ribbon_df[YMIN] = float(BASE)
bench_color = IMPRINT_PALETTE[groups.index(BENCHMARK)] if BENCHMARK in groups else INK_SOFT

x_max = df[DATE].max() + pd.Timedelta(days=45)

plot = (
    ggplot(df, aes(x=DATE, y=REBASED, color=SYMBOL))
    + geom_ribbon(
        data=ribbon_df, mapping=aes(x=DATE, ymin=YMIN, ymax=YMAX), fill=bench_color, alpha=0.10, inherit_aes=False
    )
    + geom_hline(yintercept=BASE, linetype="dashed", color=INK_SOFT, size=0.6)
    + geom_line(data=others_df, size=1.1)
    + geom_line(data=bench_df, size=1.7)
    + geom_point(data=last_df, size=2.5, show_legend=False)
    + geom_text(data=last_df, mapping=aes(x=LABEL_DATE, label=LABEL), size=8, ha="left", show_legend=False)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=groups)
    + scale_x_date(date_labels="%b '%y", date_breaks="2 months", limits=[df[DATE].min(), x_max])
    + labs(title="line-stock-comparison · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_blank(),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        axis_text_x=element_text(angle=45, ha="right"),
        plot_title=element_text(color=INK, size=12, fontweight="bold"),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_text(color=INK, size=9),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
