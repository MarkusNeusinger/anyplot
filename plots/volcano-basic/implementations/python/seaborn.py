""" anyplot.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette for volcano plot
# Non-significant: adaptive neutral
# Down-regulated: #4467A3 (Okabe-Ito blue)
# Up-regulated: #AE3030 (Okabe-Ito orange)
NOT_SIG_COLOR = INK_MUTED
DOWN_COLOR = "#4467A3"
UP_COLOR = "#AE3030"

# Data generation
np.random.seed(42)
n_genes = 500

# Single normal distribution for log2 fold changes
log2_fold_change = np.random.normal(0, 0.8, n_genes)

# Generate p-values: correlation with fold change magnitude for realistic volcano shape
# Genes with larger fold changes tend to have lower p-values
base_pvalues = 10 ** (-(np.abs(log2_fold_change) ** 1.5) * np.random.uniform(0.8, 1.5, n_genes))
base_pvalues = np.clip(base_pvalues, 1e-10, 1.0)
neg_log10_pvalue = -np.log10(base_pvalues)

# Define significance thresholds
pval_threshold = 1.3  # -log10(0.05)
fc_threshold = 1.0  # log2(2) = 1

# Categorize genes
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

# Sort by category to plot significant genes on top
category_order = {"Not Significant": 0, "Down-regulated": 1, "Up-regulated": 2}
df["order"] = df["category"].map(category_order)
df = df.sort_values("order")

# Color palette with Okabe-Ito colors
palette = {"Not Significant": NOT_SIG_COLOR, "Down-regulated": DOWN_COLOR, "Up-regulated": UP_COLOR}

# Set seaborn theme with adaptive colors
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Scatter plot
sns.scatterplot(
    data=df,
    x="log2_fold_change",
    y="neg_log10_pvalue",
    hue="category",
    hue_order=["Not Significant", "Down-regulated", "Up-regulated"],
    palette=palette,
    s=120,
    alpha=0.6,
    edgecolor="none",
    ax=ax,
)

# Threshold lines with adaptive colors
ax.axhline(y=pval_threshold, color=INK_SOFT, linestyle="--", linewidth=2, alpha=0.5)
ax.axvline(x=fc_threshold, color=INK_SOFT, linestyle="--", linewidth=2, alpha=0.5)
ax.axvline(x=-fc_threshold, color=INK_SOFT, linestyle="--", linewidth=2, alpha=0.5)

# Labels and styling
ax.set_xlabel("Log2 Fold Change", fontsize=20, color=INK, fontweight="medium")
ax.set_ylabel("-Log10(p-value)", fontsize=20, color=INK, fontweight="medium")
ax.set_title("volcano-basic · seaborn · anyplot.ai", fontsize=24, color=INK, fontweight="medium")
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Legend styling
legend = ax.legend(
    title="Significance Status", fontsize=14, title_fontsize=16, loc="upper right", framealpha=0.95, edgecolor=INK_SOFT
)
legend.get_frame().set_facecolor(ELEVATED_BG)
for text in legend.get_texts():
    text.set_color(INK)
legend.get_title().set_color(INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
