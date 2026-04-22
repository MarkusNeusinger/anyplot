""" pyplots.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Simulated differential expression results
np.random.seed(42)
n_genes = 500

# Generate log2 fold changes (centered around 0, some extreme values)
log2_fold_change = np.concatenate(
    [
        np.random.normal(0, 0.5, n_genes - 60),  # Most genes: no change
        np.random.normal(-2.5, 0.5, 30),  # Down-regulated
        np.random.normal(2.5, 0.5, 30),  # Up-regulated
    ]
)

# Generate p-values (correlated with fold change magnitude for realism)
base_pvalues = 10 ** (-np.abs(log2_fold_change) * np.random.uniform(0.5, 2, n_genes))
base_pvalues = np.clip(base_pvalues, 1e-10, 1.0)
neg_log10_pvalue = -np.log10(base_pvalues)

# Define significance thresholds
pval_threshold = 1.3  # -log10(0.05)
fc_threshold = 1.0  # log2(2) = 1

# Categorize genes using numpy vectorized conditions
categories = np.where(
    neg_log10_pvalue < pval_threshold,
    "Not Significant",
    np.where(
        log2_fold_change > fc_threshold,
        "Up-regulated",
        np.where(log2_fold_change < -fc_threshold, "Down-regulated", "Not Significant"),
    ),
)

# Create DataFrame
df = pd.DataFrame({"log2_fold_change": log2_fold_change, "neg_log10_pvalue": neg_log10_pvalue, "category": categories})

# Sort so significant points are plotted on top
category_order = {"Not Significant": 0, "Down-regulated": 1, "Up-regulated": 2}
df["order"] = df["category"].map(category_order)
df = df.sort_values("order")

# Color palette matching specification
palette = {
    "Not Significant": "#888888",
    "Down-regulated": "#306998",  # Python Blue
    "Up-regulated": "#E63946",  # Red for up-regulated
}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Scatter plot using seaborn
sns.scatterplot(
    data=df,
    x="log2_fold_change",
    y="neg_log10_pvalue",
    hue="category",
    hue_order=["Not Significant", "Down-regulated", "Up-regulated"],
    palette=palette,
    s=100,
    alpha=0.7,
    edgecolor="none",
    ax=ax,
    legend=True,
)

# Threshold lines
ax.axhline(y=pval_threshold, color="#333333", linestyle="--", linewidth=2, alpha=0.7)
ax.axvline(x=fc_threshold, color="#333333", linestyle="--", linewidth=2, alpha=0.7)
ax.axvline(x=-fc_threshold, color="#333333", linestyle="--", linewidth=2, alpha=0.7)

# Add threshold annotations
ax.text(ax.get_xlim()[1] - 0.3, pval_threshold + 0.3, "p = 0.05", fontsize=14, ha="right", color="#333333")
ax.text(fc_threshold + 0.1, ax.get_ylim()[1] - 0.5, "FC = 2", fontsize=14, ha="left", color="#333333")
ax.text(-fc_threshold - 0.1, ax.get_ylim()[1] - 0.5, "FC = 0.5", fontsize=14, ha="right", color="#333333")

# Labels and styling
ax.set_xlabel("Log2 Fold Change", fontsize=20)
ax.set_ylabel("-Log10(p-value)", fontsize=20)
ax.set_title("volcano-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Legend styling
ax.legend(title="Significance", fontsize=14, title_fontsize=16, loc="upper right", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
