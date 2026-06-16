""" anyplot.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme-adaptive colors
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (colorblind-safe)
OKABE_ITO_DOWN = "#4467A3"  # imprint blue — down-regulated (cool)
OKABE_ITO_UP = "#AE3030"  # imprint red — up-regulated (warm semantic)
OKABE_ITO_NEUTRAL = "#888888"  # Gray for not significant

# Data - Simulated differential expression results
np.random.seed(42)
n_genes = 500

# Generate log2 fold changes (mostly near zero with some extremes)
log2_fc = np.concatenate(
    [
        np.random.normal(0, 0.4, n_genes - 100),  # Unchanged genes
        np.random.normal(2.2, 0.6, 50),  # Up-regulated
        np.random.normal(-2.2, 0.6, 50),  # Down-regulated
    ]
)

# Generate p-values (strongly correlated with fold change magnitude)
# Higher fold change = lower p-value (more significant)
neg_log10_pval = np.zeros(n_genes)
for i, fc in enumerate(log2_fc):
    if abs(fc) > 1.5:  # Large fold changes get significant p-values
        neg_log10_pval[i] = np.random.uniform(1.5, 3.5)
    elif abs(fc) > 1.0:  # Moderate fold changes get borderline p-values
        neg_log10_pval[i] = np.random.uniform(0.8, 2.0)
    else:  # Small fold changes get non-significant p-values
        neg_log10_pval[i] = np.random.uniform(0.1, 1.5)

# Determine significance status
p_threshold = 1.3  # -log10(0.05)
fc_threshold = 1.0  # log2(2) = 1

significance = []
for fc, nlp in zip(log2_fc, neg_log10_pval, strict=False):
    if nlp > p_threshold and fc > fc_threshold:
        significance.append("Up-regulated")
    elif nlp > p_threshold and fc < -fc_threshold:
        significance.append("Down-regulated")
    else:
        significance.append("Not significant")

# Create DataFrame
df = pd.DataFrame({"log2_fold_change": log2_fc, "neg_log10_pvalue": neg_log10_pval, "significance": significance})

# Create volcano plot
plot = (
    ggplot(df, aes(x="log2_fold_change", y="neg_log10_pvalue", color="significance"))
    + geom_point(aes(color="significance"), size=4, alpha=0.7)
    + geom_hline(yintercept=p_threshold, linetype="dashed", color=INK_SOFT, size=1)
    + geom_vline(xintercept=-fc_threshold, linetype="dashed", color=INK_SOFT, size=1)
    + geom_vline(xintercept=fc_threshold, linetype="dashed", color=INK_SOFT, size=1)
    + scale_color_manual(
        values=[OKABE_ITO_DOWN, OKABE_ITO_NEUTRAL, OKABE_ITO_UP],
        breaks=["Down-regulated", "Not significant", "Up-regulated"],
    )
    + labs(x="Log2 Fold Change", y="-Log10(p-value)", title="volcano-basic · letsplot · anyplot.ai", color="Status")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor=element_line(color=INK_SOFT, size=0.2),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, face="bold", color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale=3 gives 4800x2700)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, f"plot-{THEME}.html", path=".")
