""" anyplot.ai
confusion-matrix: Confusion Matrix Heatmap
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Multi-class classification results for a sentiment analysis model
np.random.seed(42)
class_names = ["Negative", "Neutral", "Positive", "Mixed"]

# Create realistic confusion matrix with strong diagonal (good model)
# but with some systematic confusion patterns
confusion_matrix = np.array(
    [
        [156, 12, 5, 8],  # Negative: mostly correct, some confused with Neutral
        [18, 142, 15, 10],  # Neutral: hardest to classify, confused with all
        [3, 8, 168, 6],  # Positive: good accuracy
        [11, 14, 9, 125],  # Mixed: often confused with Neutral
    ]
)

# Configure theme-adaptive styling
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

# Create figure (square format for symmetric matrix)
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Create heatmap with annotations
sns.heatmap(
    confusion_matrix,
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=class_names,
    yticklabels=class_names,
    square=True,
    linewidths=2,
    linecolor=PAGE_BG,
    cbar_kws={"shrink": 0.8},
    annot_kws={"size": 20, "weight": "bold"},
    ax=ax,
)

# Style the colorbar
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=16, colors=INK_SOFT)
cbar.ax.set_ylabel("Count", fontsize=18, labelpad=15, color=INK)

# Labels and title
ax.set_xlabel("Predicted Label", fontsize=22, labelpad=15, color=INK)
ax.set_ylabel("True Label", fontsize=22, labelpad=15, color=INK)
ax.set_title("Sentiment Analysis · confusion-matrix · seaborn · anyplot.ai", fontsize=24, pad=20, color=INK)

# Style tick labels
ax.tick_params(axis="both", labelsize=18, colors=INK_SOFT)

# Rotate x-axis labels for better readability
plt.xticks(rotation=45, ha="right")
plt.yticks(rotation=0)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
