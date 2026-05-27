""" anyplot.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for significance categories
COLOR_DOWNREG = "#4467A3"  # Blue
COLOR_UPREG = "#C475FD"  # Vermillion
COLOR_NONSIG = "#888888"  # Neutral gray

# Data - simulated differential expression results
np.random.seed(42)
n_genes = 2000

# Generate log2 fold changes (centered around 0)
log2_fc = np.random.normal(0, 1.5, n_genes)

# Generate p-values (most non-significant, some significant)
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

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot non-significant points first (gray)
ax.scatter(
    log2_fc[non_sig],
    neg_log10_pval[non_sig],
    c=COLOR_NONSIG,
    s=120,
    alpha=0.5,
    label="Not significant",
    edgecolors="none",
)

# Plot significant down-regulated (blue)
ax.scatter(
    log2_fc[sig_down],
    neg_log10_pval[sig_down],
    c=COLOR_DOWNREG,
    s=150,
    alpha=0.8,
    label="Down-regulated",
    edgecolors="none",
)

# Plot significant up-regulated (vermillion)
ax.scatter(
    log2_fc[sig_up], neg_log10_pval[sig_up], c=COLOR_UPREG, s=150, alpha=0.8, label="Up-regulated", edgecolors="none"
)

# Add threshold lines
ax.axhline(y=pval_threshold, color=INK_SOFT, linestyle="--", linewidth=1.5, alpha=0.4, zorder=1)
ax.axvline(x=fc_threshold, color=INK_SOFT, linestyle="--", linewidth=1.5, alpha=0.4, zorder=1)
ax.axvline(x=-fc_threshold, color=INK_SOFT, linestyle="--", linewidth=1.5, alpha=0.4, zorder=1)

# Label top significant genes
top_up_idx = np.where(sig_up)[0]
if len(top_up_idx) > 0:
    top_up_scores = neg_log10_pval[top_up_idx] + np.abs(log2_fc[top_up_idx])
    top_up = top_up_idx[np.argsort(top_up_scores)[-5:]]
    for idx in top_up:
        ax.annotate(
            f"Gene_{idx}",
            (log2_fc[idx], neg_log10_pval[idx]),
            fontsize=13,
            ha="left",
            va="bottom",
            xytext=(5, 5),
            textcoords="offset points",
            color=INK,
        )

top_down_idx = np.where(sig_down)[0]
if len(top_down_idx) > 0:
    top_down_scores = neg_log10_pval[top_down_idx] + np.abs(log2_fc[top_down_idx])
    top_down = top_down_idx[np.argsort(top_down_scores)[-5:]]
    for idx in top_down:
        ax.annotate(
            f"Gene_{idx}",
            (log2_fc[idx], neg_log10_pval[idx]),
            fontsize=13,
            ha="right",
            va="bottom",
            xytext=(-5, 5),
            textcoords="offset points",
            color=INK,
        )

# Styling
ax.set_xlabel("Log₂ Fold Change", fontsize=20, color=INK)
ax.set_ylabel("-Log₁₀ (p-value)", fontsize=20, color=INK)
ax.set_title("volcano-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Spines and grid
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)

# Legend styling
leg = ax.legend(fontsize=16, loc="upper left", framealpha=0.95)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

# Set axis limits with padding
x_max = max(abs(log2_fc.min()), abs(log2_fc.max())) * 1.1
ax.set_xlim(-x_max, x_max)
ax.set_ylim(0, neg_log10_pval.max() * 1.1)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
