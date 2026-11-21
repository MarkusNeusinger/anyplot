""" anyplot.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_DOWN = IMPRINT_PALETTE[2]  # blue: down-regulated
COLOR_UP = IMPRINT_PALETTE[4]  # matte red: up-regulated
COLOR_NEUTRAL = INK_MUTED  # theme-adaptive muted gray: not significant

# Constants
P_THRESHOLD = 1.3  # -log10(0.05)
FC_THRESHOLD = 1.0  # log2(2): two-fold change
UP, DOWN, NS = "Up-regulated", "Down-regulated", "Not significant"

# Columns: set these to your table's column names
LOG2FC = "Log2 fold change"  # role: log2_fold_change
NLOGP = "-Log10(p-value)"  # role: neg_log10_pvalue
STATUS = "Status"  # role: significant

# Data: replace this block with your own table, for example df = pd.read_csv("de_results.csv")
np.random.seed(42)
n_genes = 500

log2_fc = np.concatenate(
    [
        np.random.normal(0, 0.4, n_genes - 100),  # unchanged genes
        np.random.normal(2.2, 0.6, 50),  # up-regulated
        np.random.normal(-2.2, 0.6, 50),  # down-regulated
    ]
)

# Larger fold changes get smaller p-values
neg_log10_pval = np.zeros(n_genes)
for i, fc in enumerate(log2_fc):
    if abs(fc) > 1.5:
        neg_log10_pval[i] = np.random.uniform(1.5, 3.5)
    elif abs(fc) > 1.0:
        neg_log10_pval[i] = np.random.uniform(0.8, 2.0)
    else:
        neg_log10_pval[i] = np.random.uniform(0.1, 1.5)

df = pd.DataFrame({LOG2FC: log2_fc, NLOGP: neg_log10_pval})
significant = df[NLOGP] > P_THRESHOLD
df[STATUS] = np.select(
    [significant & (df[LOG2FC] > FC_THRESHOLD), significant & (df[LOG2FC] < -FC_THRESHOLD)], [UP, DOWN], default=NS
)

# Plot: reads only df and the constants above
plot = (
    ggplot(df, aes(x=LOG2FC, y=NLOGP, color=STATUS))
    + geom_point(size=2.5, alpha=0.6)
    + geom_hline(yintercept=P_THRESHOLD, linetype="dashed", color=INK_SOFT, size=0.6)
    + geom_vline(xintercept=-FC_THRESHOLD, linetype="dashed", color=INK_SOFT, size=0.6)
    + geom_vline(xintercept=FC_THRESHOLD, linetype="dashed", color=INK_SOFT, size=0.6)
    + scale_color_manual(values=[COLOR_DOWN, COLOR_NEUTRAL, COLOR_UP], breaks=[DOWN, NS, UP])
    + labs(title="volcano-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3),
        panel_grid_minor=element_line(color=INK, size=0.2),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=16, face="bold", color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Output: PNG at 3200 x 1800 (scale 4), HTML for interactivity
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
