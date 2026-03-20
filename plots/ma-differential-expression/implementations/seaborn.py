""" pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from statsmodels.nonparametric.smoothers_lowess import lowess


# Data - Simulated RNA-seq differential expression results (~15,000 genes)
np.random.seed(42)
n_genes = 15000

mean_expression = np.random.exponential(scale=3, size=n_genes) + 1
log_fold_change = np.random.normal(0, 0.5, n_genes)

# Add truly differentially expressed genes (~8% of genes)
n_de = int(n_genes * 0.08)
de_indices = np.random.choice(n_genes, n_de, replace=False)
log_fold_change[de_indices] += np.random.choice([-1, 1], n_de) * np.random.uniform(1.5, 4, n_de)

# Simulate p-values: DE genes get small p-values, others get uniform
p_values = np.ones(n_genes)
p_values[de_indices] = 10 ** (-np.random.uniform(2, 10, n_de))
p_values[~np.isin(np.arange(n_genes), de_indices)] = np.random.uniform(0.01, 1.0, n_genes - n_de)

significant = p_values < 0.05

# Gene names for top hits (select genes spread across expression range)
gene_names = [f"Gene{i}" for i in range(n_genes)]
top_gene_labels = ["BRCA1", "TP53", "MYC", "EGFR", "VEGFA", "IL6"]
sig_indices = np.where(significant)[0]
sig_abs_lfc = np.abs(log_fold_change[sig_indices])
top_sig = sig_indices[np.argsort(sig_abs_lfc)[-len(top_gene_labels) :]]
for i, idx in enumerate(top_sig):
    gene_names[idx] = top_gene_labels[i]

df = pd.DataFrame(
    {
        "mean_expression": mean_expression,
        "log_fold_change": log_fold_change,
        "significant": significant,
        "gene_name": gene_names,
    }
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Non-significant genes
ns_data = df[~df["significant"]]
sns.scatterplot(
    x=ns_data["mean_expression"],
    y=ns_data["log_fold_change"],
    color="#BFBFBF",
    alpha=0.25,
    s=25,
    edgecolor="none",
    ax=ax,
    label="Not significant",
)

# Significant genes
sig_data = df[df["significant"]]
sns.scatterplot(
    x=sig_data["mean_expression"],
    y=sig_data["log_fold_change"],
    color="#E74C3C",
    alpha=0.5,
    s=45,
    edgecolor="white",
    linewidth=0.3,
    ax=ax,
    label="Significant (adj. p < 0.05)",
)

# Reference lines
ax.axhline(y=0, color="#306998", linewidth=2.5, alpha=0.7)
ax.axhline(y=1, color="#306998", linewidth=1.5, linestyle="--", alpha=0.6, label="±1 log₂FC threshold")
ax.axhline(y=-1, color="#306998", linewidth=1.5, linestyle="--", alpha=0.6)

# LOESS smoothing curve
loess_result = lowess(log_fold_change, mean_expression, frac=0.3)
ax.plot(loess_result[:, 0], loess_result[:, 1], color="#FFD43B", linewidth=3.5, alpha=0.9, label="LOESS trend")

# Label top differentially expressed genes
offsets = [(15, 18), (-15, -22), (15, -20), (-15, 18), (20, 15), (-20, -18)]
for i, idx in enumerate(top_sig):
    x_off, y_off = offsets[i % len(offsets)]
    ax.annotate(
        gene_names[idx],
        xy=(mean_expression[idx], log_fold_change[idx]),
        xytext=(x_off, y_off),
        textcoords="offset points",
        fontsize=13,
        fontweight="bold",
        color="#2C3E50",
        arrowprops={"arrowstyle": "-", "color": "#2C3E50", "lw": 1},
    )

# Style
ax.set_xlabel("Mean Expression (A)", fontsize=20)
ax.set_ylabel("Log₂ Fold Change (M)", fontsize=20)
ax.set_title("ma-differential-expression · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.legend(fontsize=14, loc="upper left", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
