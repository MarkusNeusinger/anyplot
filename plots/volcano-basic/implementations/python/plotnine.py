""" anyplot.ai
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

# Data - simulated differential gene expression results
np.random.seed(42)
n_genes = 500

# Generate log2 fold changes (centered around 0 with some outliers)
log2_fold_change = np.concatenate(
    [
        np.random.normal(0, 0.8, 400),  # Most genes have small changes
        np.random.normal(-2.5, 0.5, 50),  # Down-regulated genes
        np.random.normal(2.5, 0.5, 50),  # Up-regulated genes
    ]
)

# Generate p-values with a realistic range (avoiding extreme values)
pvalues = np.concatenate(
    [
        np.random.uniform(0.05, 1.0, 400),  # Most genes not significant
        np.random.uniform(0.0001, 0.01, 50),  # Down-regulated significant
        np.random.uniform(0.0001, 0.01, 50),  # Up-regulated significant
    ]
)

neg_log10_pvalue = -np.log10(pvalues)

# Create gene labels
gene_labels = [f"Gene_{i + 1}" for i in range(n_genes)]

# Determine significance status based on thresholds
significance_threshold = -np.log10(0.05)  # ~1.3
fold_change_threshold = 1.0

status = []
for fc, nlp in zip(log2_fold_change, neg_log10_pvalue, strict=True):
    if nlp > significance_threshold and fc > fold_change_threshold:
        status.append("Up-regulated")
    elif nlp > significance_threshold and fc < -fold_change_threshold:
        status.append("Down-regulated")
    else:
        status.append("Not significant")

# Create DataFrame
df = pd.DataFrame(
    {
        "log2_fold_change": log2_fold_change,
        "neg_log10_pvalue": neg_log10_pvalue,
        "label": gene_labels,
        "status": pd.Categorical(status, categories=["Down-regulated", "Not significant", "Up-regulated"]),
    }
)

# Identify top genes to label (top 4 by significance in each direction, better spacing)
df_up = df[df["status"] == "Up-regulated"].nlargest(3, "neg_log10_pvalue")
df_down = df[df["status"] == "Down-regulated"].nlargest(3, "neg_log10_pvalue")
df_labels = pd.concat([df_up, df_down])

# Okabe-Ito palette (blue for down, gray for not significant, orange for up)
color_map = {
    "Down-regulated": "#4467A3",  # Okabe-Ito blue
    "Not significant": "#888888",  # neutral gray
    "Up-regulated": "#AE3030",  # Okabe-Ito orange
}

# Create volcano plot
plot = (
    ggplot(df, aes(x="log2_fold_change", y="neg_log10_pvalue", color="status"))
    + geom_point(size=3, alpha=0.7)
    + geom_hline(yintercept=significance_threshold, linetype="dashed", color=INK_SOFT, size=0.8)
    + geom_vline(xintercept=-fold_change_threshold, linetype="dashed", color=INK_SOFT, size=0.8)
    + geom_vline(xintercept=fold_change_threshold, linetype="dashed", color=INK_SOFT, size=0.8)
    + geom_text(data=df_labels, mapping=aes(label="label"), size=10, nudge_y=0.4, nudge_x=0.15, color=INK_SOFT)
    + scale_color_manual(values=color_map)
    + labs(
        x="Log2 Fold Change", y="-Log10(p-value)", title="volcano-basic · plotnine · anyplot.ai", color="Significance"
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10, linetype="solid"),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        text=element_text(size=14),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
    )
)

# Save plot
plot.save(f"plot-{THEME}.png", dpi=300)
