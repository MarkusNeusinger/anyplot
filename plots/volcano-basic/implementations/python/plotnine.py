"""anyplot.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_point,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
MUTED = "#8A8A82"  # neutral gray for the non-significant mass

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
P_THRESHOLD = 0.05  # significance cutoff on the p-value
FC_THRESHOLD = 1.0  # log2 fold change cutoff (2-fold change)
N_LABELS = 3  # top significant features named per direction
DOWN, NEUTRAL, UP = "Down-regulated", "Not significant", "Up-regulated"

# Columns: set these to your table's column names
LOG2FC = "Log2 fold change"  # role: log2_fold_change
NEGLOGP = "-Log10(p-value)"  # role: neg_log10_pvalue
GENE = "Gene"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("de_results.csv")
np.random.seed(42)
fold_change = np.concatenate(
    [
        np.random.normal(0, 0.8, 400),  # most genes change little
        np.random.normal(-2.5, 0.5, 50),  # down-regulated genes
        np.random.normal(2.5, 0.5, 50),  # up-regulated genes
    ]
)
p_values = np.concatenate(
    [
        np.random.uniform(0.05, 1.0, 400),  # most genes not significant
        np.random.uniform(0.0001, 0.01, 50),  # down-regulated, significant
        np.random.uniform(0.0001, 0.01, 50),  # up-regulated, significant
    ]
)
df = pd.DataFrame(
    {LOG2FC: fold_change, NEGLOGP: -np.log10(p_values), GENE: [f"Gene_{i + 1}" for i in range(len(fold_change))]}
)

# Plot: reads only df and the constants above
p_cutoff = -np.log10(P_THRESHOLD)
significant = df[NEGLOGP] > p_cutoff
status = np.select(
    [significant & (df[LOG2FC] > FC_THRESHOLD), significant & (df[LOG2FC] < -FC_THRESHOLD)], [UP, DOWN], NEUTRAL
)
df["Significance"] = pd.Categorical(status, categories=[DOWN, NEUTRAL, UP])

top_up = df[df["Significance"] == UP].nlargest(N_LABELS, NEGLOGP)
top_down = df[df["Significance"] == DOWN].nlargest(N_LABELS, NEGLOGP)
df_labels = pd.concat([top_up, top_down])
label_offset = df[NEGLOGP].max() * 0.04

plot = (
    ggplot(df, aes(x=LOG2FC, y=NEGLOGP, color="Significance"))
    + geom_point(size=1.8, alpha=0.65)
    + geom_hline(yintercept=p_cutoff, linetype="dashed", color=INK_SOFT, size=0.5)
    + geom_vline(xintercept=-FC_THRESHOLD, linetype="dashed", color=INK_SOFT, size=0.5)
    + geom_vline(xintercept=FC_THRESHOLD, linetype="dashed", color=INK_SOFT, size=0.5)
    + geom_text(data=df_labels, mapping=aes(label=GENE), size=6, nudge_y=label_offset, color=INK_SOFT)
    + scale_color_manual(values=[IMPRINT_PALETTE[2], MUTED, IMPRINT_PALETTE[4]], limits=[DOWN, NEUTRAL, UP])
    + labs(title="volcano-basic · python · plotnine · anyplot.ai", color="Significance")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        text=element_text(size=7),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
