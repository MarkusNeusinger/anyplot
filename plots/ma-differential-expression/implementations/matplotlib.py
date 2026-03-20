""" pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import UnivariateSpline


# Data
np.random.seed(42)
n_genes = 15000

mean_expression = np.random.exponential(scale=3.0, size=n_genes) + 0.5
log_fold_change = np.random.normal(0, 0.4, size=n_genes)

n_upregulated = 400
n_downregulated = 350
up_idx = np.random.choice(n_genes, n_upregulated, replace=False)
remaining = np.setdiff1d(np.arange(n_genes), up_idx)
down_idx = np.random.choice(remaining, n_downregulated, replace=False)

log_fold_change[up_idx] = np.random.normal(2.5, 0.8, n_upregulated)
log_fold_change[down_idx] = np.random.normal(-2.5, 0.8, n_downregulated)

significant = np.zeros(n_genes, dtype=bool)
significant[up_idx] = True
significant[down_idx] = True

top_up = up_idx[np.argsort(log_fold_change[up_idx])[-4:]]
top_down = down_idx[np.argsort(log_fold_change[down_idx])[:4]]
label_idx = np.concatenate([top_up, top_down])
label_names = ["BRCA1", "TP53", "MYC", "EGFR", "PTEN", "RB1", "APC", "KRAS"]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

nonsig_mask = ~significant
ax.scatter(
    mean_expression[nonsig_mask],
    log_fold_change[nonsig_mask],
    s=12,
    alpha=0.15,
    color="#AAAAAA",
    edgecolors="none",
    rasterized=True,
    label="Not significant",
)

ax.scatter(
    mean_expression[significant],
    log_fold_change[significant],
    s=30,
    alpha=0.45,
    color="#C0392B",
    edgecolors="white",
    linewidth=0.3,
    rasterized=True,
    label="Significant (adj. p < 0.05)",
)

# Reference lines
ax.axhline(y=0, color="#333333", linewidth=1.5, zorder=1)
ax.axhline(y=1, color="#666666", linewidth=1.0, linestyle="--", alpha=0.6, zorder=1)
ax.axhline(y=-1, color="#666666", linewidth=1.0, linestyle="--", alpha=0.6, zorder=1)

# LOESS smoothing curve
sorted_idx = np.argsort(mean_expression)
x_sorted = mean_expression[sorted_idx]
y_sorted = log_fold_change[sorted_idx]

bin_count = 80
bin_edges = np.linspace(x_sorted.min(), np.percentile(x_sorted, 98), bin_count + 1)
bin_centers = []
bin_means = []
for i in range(bin_count):
    mask = (x_sorted >= bin_edges[i]) & (x_sorted < bin_edges[i + 1])
    if mask.sum() > 10:
        bin_centers.append((bin_edges[i] + bin_edges[i + 1]) / 2)
        bin_means.append(np.mean(y_sorted[mask]))

bin_centers = np.array(bin_centers)
bin_means = np.array(bin_means)
spline = UnivariateSpline(bin_centers, bin_means, s=len(bin_centers) * 0.5)
x_smooth = np.linspace(bin_centers.min(), bin_centers.max(), 200)
y_smooth = spline(x_smooth)
ax.plot(x_smooth, y_smooth, color="#306998", linewidth=3, alpha=0.8, label="LOESS trend")

# Gene labels
for i, name in zip(label_idx, label_names, strict=False):
    ax.annotate(
        name,
        (mean_expression[i], log_fold_change[i]),
        fontsize=11,
        fontweight="bold",
        fontstyle="italic",
        xytext=(8, 6),
        textcoords="offset points",
        color="#222222",
    )

# Style
ax.set_xlabel("Mean Expression (A)", fontsize=20)
ax.set_ylabel("Log₂ Fold Change (M)", fontsize=20)
ax.set_title("ma-differential-expression · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.legend(fontsize=16, loc="upper left", framealpha=0.9, edgecolor="none", fancybox=False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
