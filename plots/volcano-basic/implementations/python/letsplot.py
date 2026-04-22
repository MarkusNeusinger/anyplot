""" pyplots.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

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
for fc, nlp in zip(log2_fc, neg_log10_pval):
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
    + geom_hline(yintercept=p_threshold, linetype="dashed", color="#666666", size=1)
    + geom_vline(xintercept=-fc_threshold, linetype="dashed", color="#666666", size=1)
    + geom_vline(xintercept=fc_threshold, linetype="dashed", color="#666666", size=1)
    + scale_color_manual(
        values=["#306998", "#888888", "#DC2626"], breaks=["Down-regulated", "Not significant", "Up-regulated"]
    )
    + labs(x="Log2 Fold Change", y="-Log10(p-value)", title="volcano-basic · letsplot · pyplots.ai", color="Status")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale=3 gives 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
