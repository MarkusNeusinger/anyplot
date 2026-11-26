"""anyplot.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_histogram,
    geom_line,
    geom_vline,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
TAIL_SIGMAS = 2  # tail regions start this many standard deviations from the mean
N_BINS = 30

# Columns: set these to your table's column names
DATE = "Date"  # role: date
RETURNS = "Daily Returns (%)"  # role: returns

# Data: replace this block with your own table, for example df = pd.read_csv("returns.csv")
np.random.seed(42)
n_days = 252
normal_returns = np.random.normal(0.0005, 0.015, int(n_days * 0.9))
fat_tail_returns = np.random.normal(0, 0.04, int(n_days * 0.1))
returns = np.concatenate([normal_returns, fat_tail_returns])
np.random.shuffle(returns)
df = pd.DataFrame({DATE: pd.bdate_range("2024-01-02", periods=len(returns)), RETURNS: returns * 100})

# Plot: reads only df and the constants above
returns_pct = df[RETURNS]
mean_ret = returns_pct.mean()
std_ret = returns_pct.std(ddof=0)
lower_tail = mean_ret - TAIL_SIGMAS * std_ret
upper_tail = mean_ret + TAIL_SIGMAS * std_ret

# Tail classification feeds the fill aesthetic
REGION = "Region"
df[REGION] = pd.cut(
    returns_pct, bins=[-np.inf, lower_tail, upper_tail, np.inf], labels=["Left Tail", "Center", "Right Tail"]
)

# Normal distribution overlay (count scale to match histogram)
NORMAL_FIT = "Normal fit (count)"
x_range = np.linspace(returns_pct.min() - 1, returns_pct.max() + 1, 300)
bin_width = (returns_pct.max() - returns_pct.min()) / N_BINS
normal_scaled = stats.norm.pdf(x_range, mean_ret, std_ret) * len(returns_pct) * bin_width
df_normal = pd.DataFrame({RETURNS: x_range, NORMAL_FIT: normal_scaled})

stats_label = (
    f"Mean: {mean_ret:.2f}%\nStd Dev: {std_ret:.2f}%\n"
    f"Skewness: {stats.skew(returns_pct):.2f}\nExc. Kurtosis: {stats.kurtosis(returns_pct):.2f}"
)

# Imprint: center green (position 1), both tails purple (position 2)
fill_colors = {"Left Tail": IMPRINT_PALETTE[1], "Center": IMPRINT_PALETTE[0], "Right Tail": IMPRINT_PALETTE[1]}

plot = (
    ggplot(df, aes(x=RETURNS, fill=REGION))
    + geom_histogram(bins=N_BINS, color=PAGE_BG, alpha=0.85, size=0.3)
    + geom_line(
        data=df_normal, mapping=aes(x=RETURNS, y=NORMAL_FIT), color=IMPRINT_PALETTE[2], size=1.2, inherit_aes=False
    )
    + geom_vline(xintercept=mean_ret, linetype="dashed", color=INK, size=0.8)
    + geom_vline(xintercept=lower_tail, linetype="dotted", color=IMPRINT_PALETTE[1], size=0.8)
    + geom_vline(xintercept=upper_tail, linetype="dotted", color=IMPRINT_PALETTE[1], size=0.8)
    + scale_fill_manual(values=fill_colors, name="Region")
    + annotate(
        "label",
        x=returns_pct.max() - 0.5,
        y=max(normal_scaled) * 0.92,
        label=stats_label,
        ha="right",
        va="top",
        size=9,
        fill=ELEVATED_BG,
        color=INK,
        label_size=0.3,
        label_padding=0.4,
    )
    + labs(x=RETURNS, y="Frequency", title="histogram-returns-distribution · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        plot_title=element_text(color=INK, size=12),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_text=element_text(color=INK_SOFT, size=9),
        legend_title=element_text(color=INK, size=9),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
