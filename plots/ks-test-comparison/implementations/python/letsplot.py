"""anyplot.ai
ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-29
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    arrow,
    coord_cartesian,
    element_blank,
    element_line,
    element_markdown,
    element_rect,
    element_text,
    geom_ribbon,
    geom_segment,
    geom_step,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy import stats


LetsPlot.setup_html()

# Theme tokens — Imprint palette chrome (theme-adaptive)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — hybrid-v3 sort
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ANYPLOT_AMBER = "#DDCC77"  # warning / caution semantic anchor (outside categorical pool)

# Columns: set these to your table's column names (one numeric column per sample)
GOOD = "Good Customers"  # role: sample1
BAD = "Bad Customers"  # role: sample2

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
# Credit scoring: score distributions of good and bad customers (samples may differ in size)
np.random.seed(42)
good_scores = np.clip(np.random.normal(loc=620, scale=80, size=500), 300, 850)
bad_scores = np.clip(np.random.normal(loc=520, scale=90, size=300), 300, 850)
df = pd.DataFrame({GOOD: pd.Series(good_scores), BAD: pd.Series(bad_scores)})

# Plot: reads only df and the constants above
SCORE = "Credit Score (points)"
ECDF = "Cumulative Proportion"
GROUP = "Group"
LOW, HIGH = "low", "high"

samples = {name: np.sort(df[name].dropna().to_numpy()) for name in (GOOD, BAD)}
good_sorted, bad_sorted = samples[GOOD], samples[BAD]

# ECDF step frames, one row per observation
df_ecdf = pd.concat(
    [
        pd.DataFrame({SCORE: values, ECDF: np.arange(1, len(values) + 1) / len(values), GROUP: name})
        for name, values in samples.items()
    ],
    ignore_index=True,
)

# K-S test and the point of maximum divergence
ks_stat, p_value = stats.ks_2samp(good_sorted, bad_sorted)
all_values = np.sort(np.concatenate([good_sorted, bad_sorted]))
good_ecdf_all = np.searchsorted(good_sorted, all_values, side="right") / len(good_sorted)
bad_ecdf_all = np.searchsorted(bad_sorted, all_values, side="right") / len(bad_sorted)
max_idx = np.argmax(np.abs(good_ecdf_all - bad_ecdf_all))
max_x = all_values[max_idx]
y_lo = min(good_ecdf_all[max_idx], bad_ecdf_all[max_idx])
y_hi = max(good_ecdf_all[max_idx], bad_ecdf_all[max_idx])
ks_mid_y = (y_lo + y_hi) / 2

# Axis range from the data, with a margin
x_min, x_max = all_values[0], all_values[-1]
margin = 0.035 * (x_max - x_min)
tick_step = 100
x_breaks = list(np.arange(np.ceil(x_min / tick_step) * tick_step, x_max + 1, tick_step))
label_dx = 0.07 * (x_max - x_min)

df_ribbon = pd.DataFrame(
    {SCORE: all_values, LOW: np.minimum(good_ecdf_all, bad_ecdf_all), HIGH: np.maximum(good_ecdf_all, bad_ecdf_all)}
)
df_ks_seg = pd.DataFrame({SCORE: [max_x], ECDF: [y_lo], "xend": [max_x], "yend": [y_hi]})
df_ks_arrow = pd.DataFrame(
    {SCORE: [max_x + label_dx], ECDF: [ks_mid_y + 0.06], "xend": [max_x + 0.005 * (x_max - x_min)], "yend": [ks_mid_y]}
)
df_ks_label = pd.DataFrame(
    {SCORE: [max_x + label_dx + 0.005 * (x_max - x_min)], ECDF: [ks_mid_y + 0.08], "label": [f"D = {ks_stat:.3f}"]}
)

# Subtitle with formatted K-S stats (element_markdown renders the bold/span tags)
subtitle_text = (
    f"K-S Statistic: **{ks_stat:.3f}** | "
    f"p-value: **{p_value:.2e}** "
    f"<span style='color:{INK_MUTED}'>(highly significant)</span>"
)

title = "ks-test-comparison · python · letsplot · anyplot.ai"

# Ribbon: amber on light (caution semantic), neutral-muted on dark (amber+dark = olive)
ribbon_color = ANYPLOT_AMBER if THEME == "light" else INK_MUTED
ribbon_alpha = 0.20 if THEME == "light" else 0.30

plot = (
    ggplot(df_ecdf, aes(x=SCORE, y=ECDF))
    # Ribbon shows total divergence area (amber on light = caution; muted on dark = neutral)
    + geom_ribbon(
        data=df_ribbon,
        mapping=aes(x=SCORE, ymin=LOW, ymax=HIGH),
        fill=ribbon_color,
        alpha=ribbon_alpha,
        tooltips="none",
    )
    # Both ECDFs as step functions — Imprint positions 1 (green) and 2 (lavender)
    + geom_step(
        mapping=aes(color=GROUP),
        size=2.2,
        tooltips=layer_tooltips().line(f"@{GROUP}").line(f"Score|@{{{SCORE}}}").line(f"ECDF|@{{{ECDF}}}"),
    )
    # Dashed red segment at maximum divergence
    + geom_segment(
        data=df_ks_seg,
        mapping=aes(x=SCORE, y=ECDF, xend="xend", yend="yend"),
        color=IMPRINT_PALETTE[4],
        size=2.5,
        linetype="dashed",
        tooltips="none",
    )
    # Arrow pointing from annotation label to K-S midpoint
    + geom_segment(
        data=df_ks_arrow,
        mapping=aes(x=SCORE, y=ECDF, xend="xend", yend="yend"),
        color=IMPRINT_PALETTE[4],
        size=1.2,
        arrow=arrow(length=8, type="closed"),
        tooltips="none",
    )
    # Bold annotation of K-S statistic value — ink color for readability on both themes
    + geom_text(
        data=df_ks_label,
        mapping=aes(x=SCORE, y=ECDF, label="label"),
        color=INK,
        size=5,
        fontface="bold",
        tooltips="none",
    )
    + scale_color_manual(values={GOOD: IMPRINT_PALETTE[0], BAD: IMPRINT_PALETTE[1]})
    + labs(x=SCORE, y=ECDF, title=title, subtitle=subtitle_text, color="")
    + coord_cartesian(xlim=[x_min - margin, x_max + margin])
    + scale_x_continuous(breaks=x_breaks)
    + scale_y_continuous(limits=[0, 1.05], breaks=[0, 0.25, 0.5, 0.75, 1.0])
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_blank(),
        plot_title=element_text(size=16, face="bold", color=INK),
        plot_subtitle=element_markdown(size=12, color=INK_SOFT),
        axis_title=element_text(size=12, face="bold", color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="top",
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.3, linetype="dashed"),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
        axis_line_y=element_line(color=INK_SOFT, size=0.5),
        plot_margin=[40, 20, 20, 20],
    )
)

# Save PNG (3200×1800 via scale=4) and HTML with interactive tooltips
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
