"""anyplot.ai
ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
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
    geom_hline,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    stat_ecdf,
    theme,
    theme_minimal,
)
from scipy import stats


# Theme tokens — Imprint palette
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Semantic exception: green for Good, red for Bad customers
COLOR_GOOD = IMPRINT_PALETTE[0]  # brand green
COLOR_BAD = IMPRINT_PALETTE[4]  # matte red (bad/loss semantic anchor)

# Constants
MEDIAN_LEVEL = 0.5  # cumulative proportion of the dotted reference line
Y_TOP = 1.10  # headroom above the ECDFs for the interpretive subtitle

# Columns: set these to your table's column names
GOOD = "Good Customers"  # role: sample1
BAD = "Bad Customers"  # role: sample2
SCORE = "Credit Score (points)"  # role: extra
GROUP = "Distribution"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
df = pd.DataFrame({GOOD: np.random.beta(5, 2, 300) * 800 + 200, BAD: np.random.beta(2, 4, 300) * 800 + 200})

# Plot: reads only df and the constants above
good_sorted = np.sort(df[GOOD].dropna().to_numpy())
bad_sorted = np.sort(df[BAD].dropna().to_numpy())

# K-S test and the point of maximum divergence
ks_stat, p_value = stats.ks_2samp(good_sorted, bad_sorted)
all_values = np.sort(np.concatenate([good_sorted, bad_sorted]))
good_cdf_at_all = np.searchsorted(good_sorted, all_values, side="right") / len(good_sorted)
bad_cdf_at_all = np.searchsorted(bad_sorted, all_values, side="right") / len(bad_sorted)
max_idx = np.argmax(np.abs(good_cdf_at_all - bad_cdf_at_all))
max_x = all_values[max_idx]
y_lo = min(good_cdf_at_all[max_idx], bad_cdf_at_all[max_idx])
y_hi = max(good_cdf_at_all[max_idx], bad_cdf_at_all[max_idx])

# Long format for plotnine's ECDF stat, groups in the data's order
long = df.melt(var_name=GROUP, value_name=SCORE).dropna()
groups = df.columns.tolist()
colors = dict(zip(groups, [COLOR_GOOD, COLOR_BAD], strict=False))

# Axis range — balanced padding on both sides
x_min, x_max = all_values.min(), all_values.max()
x_pad = (x_max - x_min) * 0.04
x_mid = (x_min + x_max) / 2

# Title with required language token
title = "ks-test-comparison · python · plotnine · anyplot.ai"
ratio = 67 / len(title) if len(title) > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))

plot = (
    ggplot(long, aes(x=SCORE, color=GROUP))
    # Midpoint reference line for a structural anchor
    + geom_hline(yintercept=MEDIAN_LEVEL, color=INK_MUTED, size=0.4, linetype="dotted")
    # Max divergence vertical line
    + annotate("segment", x=max_x, xend=max_x, y=y_lo, yend=y_hi, color=COLOR_BAD, size=1.5, linetype="dashed")
    # ECDF step functions
    + stat_ecdf(geom="step", size=1.2, pad=False)
    # D label next to max divergence
    + annotate(
        "text",
        x=max_x + x_pad * 0.5,
        y=(y_lo + y_hi) / 2,
        label=f"D = {ks_stat:.3f}",
        size=11,
        ha="left",
        va="center",
        color=COLOR_BAD,
        fontweight="bold",
    )
    # Statistical summary box
    + annotate(
        "label",
        x=x_min + 0.8 * (x_max - x_min),
        y=Y_TOP * 0.04,
        label=f"K-S Statistic = {ks_stat:.3f}  |  p-value = {p_value:.2e}",
        size=10,
        ha="center",
        va="center",
        color=COLOR_BAD,
        fontweight="bold",
        fill=ELEVATED_BG,
        alpha=0.92,
        label_size=0.5,
        boxstyle="round",
    )
    # Interpretive subtitle above the ECDF area
    + annotate(
        "label",
        x=x_mid,
        y=Y_TOP * 0.96,
        label=f"Distributions are highly distinct (D = {ks_stat:.2f}) — strong evidence the groups differ"
        if p_value < 0.05
        else f"Distributions are not clearly distinct (D = {ks_stat:.2f})",
        size=9,
        ha="center",
        va="center",
        color=INK_MUTED,
        fontstyle="italic",
        fill=ELEVATED_BG,
        alpha=1.0,
        label_size=0,
        boxstyle="round",
    )
    + scale_color_manual(values=colors, limits=groups)
    + scale_y_continuous(limits=(0, Y_TOP), breaks=np.arange(0, 1.1, 0.2))
    + scale_x_continuous(limits=(x_min - x_pad, x_max + x_pad))
    + labs(x=SCORE, y="Cumulative Proportion (0–1)", title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, family="sans-serif"),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=title_fontsize, color=INK),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position=(0.15, 0.80),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, alpha=0.9, size=0.4),
        legend_key=element_rect(fill=PAGE_BG, color="none"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, alpha=0.15, size=0.3),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
        axis_line_y=element_line(color=INK_SOFT, size=0.5),
        panel_border=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
)

# Save — canonical plotnine landscape: 8×4.5 in at 400 dpi → 3200×1800 px
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
