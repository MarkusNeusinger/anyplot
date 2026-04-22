""" pyplots.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - simulated differential expression results
np.random.seed(42)
n_genes = 2000

# Generate log2 fold changes (centered around 0)
log2_fc = np.random.normal(0, 1.5, n_genes)

# Generate p-values (most non-significant, some significant)
# Use exponential distribution for realistic p-value spread
base_pvalues = np.random.exponential(0.3, n_genes)
base_pvalues = np.clip(base_pvalues, 1e-50, 1.0)

# Make genes with large fold changes more likely to be significant
significance_boost = np.abs(log2_fc) / 3
pvalues = base_pvalues * np.exp(-significance_boost * 5)
pvalues = np.clip(pvalues, 1e-50, 1.0)

# Convert to -log10(p-value)
neg_log10_pval = -np.log10(pvalues)

# Significance thresholds
pval_threshold = 1.3  # -log10(0.05)
fc_threshold = 1.0  # log2(2) = 1

# Classify points
sig_up = (neg_log10_pval > pval_threshold) & (log2_fc > fc_threshold)
sig_down = (neg_log10_pval > pval_threshold) & (log2_fc < -fc_threshold)
non_sig = ~sig_up & ~sig_down

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot non-significant points first (gray)
ax.scatter(
    log2_fc[non_sig], neg_log10_pval[non_sig], c="#888888", s=50, alpha=0.5, label="Not significant", edgecolors="none"
)

# Plot significant down-regulated (blue - Python Blue)
ax.scatter(
    log2_fc[sig_down], neg_log10_pval[sig_down], c="#306998", s=80, alpha=0.7, label="Down-regulated", edgecolors="none"
)

# Plot significant up-regulated (gold - Python Yellow)
ax.scatter(
    log2_fc[sig_up],
    neg_log10_pval[sig_up],
    c="#FFD43B",
    s=80,
    alpha=0.7,
    label="Up-regulated",
    edgecolors="white",
    linewidths=0.5,
)

# Add threshold lines
ax.axhline(y=pval_threshold, color="#333333", linestyle="--", linewidth=2, alpha=0.7)
ax.axvline(x=fc_threshold, color="#333333", linestyle="--", linewidth=2, alpha=0.7)
ax.axvline(x=-fc_threshold, color="#333333", linestyle="--", linewidth=2, alpha=0.7)

# Label top significant genes
top_up_idx = np.where(sig_up)[0]
if len(top_up_idx) > 0:
    top_up_scores = neg_log10_pval[top_up_idx] + np.abs(log2_fc[top_up_idx])
    top_up = top_up_idx[np.argsort(top_up_scores)[-5:]]
    for idx in top_up:
        ax.annotate(
            f"Gene_{idx}",
            (log2_fc[idx], neg_log10_pval[idx]),
            fontsize=12,
            ha="left",
            va="bottom",
            xytext=(5, 5),
            textcoords="offset points",
        )

top_down_idx = np.where(sig_down)[0]
if len(top_down_idx) > 0:
    top_down_scores = neg_log10_pval[top_down_idx] + np.abs(log2_fc[top_down_idx])
    top_down = top_down_idx[np.argsort(top_down_scores)[-5:]]
    for idx in top_down:
        ax.annotate(
            f"Gene_{idx}",
            (log2_fc[idx], neg_log10_pval[idx]),
            fontsize=12,
            ha="right",
            va="bottom",
            xytext=(-5, 5),
            textcoords="offset points",
        )

# Styling
ax.set_xlabel("Log₂ Fold Change", fontsize=20)
ax.set_ylabel("-Log₁₀ (p-value)", fontsize=20)
ax.set_title("volcano-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper right", framealpha=0.9)
ax.grid(True, alpha=0.3, linestyle="--")

# Set axis limits with padding
x_max = max(abs(log2_fc.min()), abs(log2_fc.max())) * 1.1
ax.set_xlim(-x_max, x_max)
ax.set_ylim(0, neg_log10_pval.max() * 1.1)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
