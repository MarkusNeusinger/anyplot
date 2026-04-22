""" pyplots.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
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
# Significant: p-value < 0.05 (neg_log10 > 1.3) AND |log2FC| > 1
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

# Identify top genes to label (top 3 by significance in each direction to avoid overlap)
df_up = df[df["status"] == "Up-regulated"].nlargest(3, "neg_log10_pvalue")
df_down = df[df["status"] == "Down-regulated"].nlargest(3, "neg_log10_pvalue")
df_labels = pd.concat([df_up, df_down])

# Create volcano plot
plot = (
    ggplot(df, aes(x="log2_fold_change", y="neg_log10_pvalue", color="status"))
    + geom_point(size=3, alpha=0.7)
    + geom_hline(yintercept=significance_threshold, linetype="dashed", color="#333333", size=0.8)
    + geom_vline(xintercept=-fold_change_threshold, linetype="dashed", color="#333333", size=0.8)
    + geom_vline(xintercept=fold_change_threshold, linetype="dashed", color="#333333", size=0.8)
    + geom_text(data=df_labels, mapping=aes(label="label"), size=10, nudge_y=0.3, color="#333333")
    + scale_color_manual(values={"Down-regulated": "#306998", "Not significant": "#888888", "Up-regulated": "#D62728"})
    + labs(
        x="Log2 Fold Change", y="-Log10(p-value)", title="volcano-basic · plotnine · pyplots.ai", color="Significance"
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
    )
)

# Save plot
plot.save("plot.png", dpi=300)
