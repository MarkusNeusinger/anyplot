""" anyplot.ai
line-stock-comparison: Stock Price Comparison Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-23
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

ANYPLOT_PALETTE = ["#009E73", "#9418DB", "#B71D27", "#16B8F3"]

# Data
np.random.seed(42)
n_days = 252
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")

symbols = ["AAPL", "GOOGL", "MSFT", "SPY"]
params = [(0.0005, 0.013), (0.0003, 0.015), (0.0006, 0.012), (0.0004, 0.008)]

dfs = []
for symbol, (drift, vol) in zip(symbols, params, strict=True):
    daily_returns = np.random.normal(drift, vol, n_days)
    prices = 100 * np.exp(np.cumsum(daily_returns))
    dfs.append(pd.DataFrame({"date": dates, "symbol": symbol, "rebased": prices}))

df = pd.concat(dfs, ignore_index=True)

# End-of-line annotation data
last_df = df.groupby("symbol").apply(lambda g: g.iloc[-1]).reset_index(drop=True)
last_df["label"] = last_df["rebased"].apply(lambda x: f"{x:.0f}")
last_df["label_date"] = last_df["date"] + pd.Timedelta(days=7)

# SPY outperformance ribbon: shades the region where SPY beats the 100 baseline
spy_df = df[df["symbol"] == "SPY"].copy()
others_df = df[df["symbol"] != "SPY"].copy()
spy_ribbon_df = spy_df[["date", "rebased"]].rename(columns={"rebased": "ymax"}).copy()
spy_ribbon_df["ymin"] = 100.0
spy_ribbon_df = spy_ribbon_df[spy_ribbon_df["ymax"] > 100]

x_max = dates[-1] + pd.Timedelta(days=30)

# Plot
plot = (
    ggplot(df, aes(x="date", y="rebased", color="symbol"))
    + geom_ribbon(
        data=spy_ribbon_df,
        mapping=aes(x="date", ymin="ymin", ymax="ymax"),
        fill=ANYPLOT_PALETTE[3],
        alpha=0.08,
        inherit_aes=False,
    )
    + geom_hline(yintercept=100, linetype="dashed", color=INK_SOFT, size=0.6)
    + geom_line(data=others_df, size=0.9)
    + geom_line(data=spy_df, size=1.6)
    + geom_point(data=last_df, size=2.5, show_legend=False)
    + geom_text(data=last_df, mapping=aes(x="label_date", label="label"), size=7, ha="left", show_legend=False)
    + scale_color_manual(values=ANYPLOT_PALETTE)
    + scale_x_date(date_labels="%b '%y", date_breaks="2 months", limits=[dates[0], x_max])
    + labs(
        x="Date",
        y="Rebased Price (Start = 100)",
        title="line-stock-comparison · python · plotnine · anyplot.ai",
        color="Symbol",
    )
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
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_text(color=INK, size=9),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
