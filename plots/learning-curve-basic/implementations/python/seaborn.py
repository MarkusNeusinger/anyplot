""" anyplot.ai
learning-curve-basic: Model Learning Curve
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-10
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

# Okabe-Ito palette (first series always #009E73)
TRAIN_COLOR = "#009E73"
VAL_COLOR = "#C475FD"

# Data - Simulating a learning curve with typical patterns
np.random.seed(42)

# Training set sizes
train_sizes = np.array([50, 100, 200, 400, 600, 800, 1000, 1200, 1500, 2000])
n_sizes = len(train_sizes)
n_folds = 5

# Generate realistic learning curve pattern:
# - Training score starts high and slightly decreases (model fits less perfectly with more data)
# - Validation score starts low and increases (model generalizes better with more data)
# - Gap narrows as training size increases

# Training scores - high and slightly decreasing
train_base = 0.98 - 0.03 * (train_sizes / train_sizes.max())
train_scores = np.array([train_base + np.random.normal(0, 0.01, n_sizes) for _ in range(n_folds)])
train_scores = np.clip(train_scores, 0.85, 1.0)

# Validation scores - starts lower, increases with more data
val_base = 0.65 + 0.25 * (1 - np.exp(-train_sizes / 500))
validation_scores = np.array([val_base + np.random.normal(0, 0.02, n_sizes) for _ in range(n_folds)])
validation_scores = np.clip(validation_scores, 0.55, 0.95)

# Calculate means and standard deviations
train_mean = train_scores.mean(axis=0)
train_std = train_scores.std(axis=0)
val_mean = validation_scores.mean(axis=0)
val_std = validation_scores.std(axis=0)

# Configure seaborn theme with adaptive colors
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
sns.set_context("talk", font_scale=1.1)

# Plot setup
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Plot training curve with confidence band
ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.2, color=TRAIN_COLOR)
sns.lineplot(
    x=train_sizes,
    y=train_mean,
    ax=ax,
    color=TRAIN_COLOR,
    linewidth=3,
    marker="o",
    markersize=10,
    label="Training Score",
)

# Plot validation curve with confidence band
ax.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.2, color=VAL_COLOR)
sns.lineplot(
    x=train_sizes, y=val_mean, ax=ax, color=VAL_COLOR, linewidth=3, marker="s", markersize=10, label="Validation Score"
)

# Labels and styling
ax.set_xlabel("Training Set Size (samples)", fontsize=20, color=INK)
ax.set_ylabel("Accuracy Score (0-1)", fontsize=20, color=INK)
ax.set_title("learning-curve-basic · seaborn · anyplot.ai", fontsize=24, color=INK, fontweight="medium")
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Set y-axis limits for better visualization
ax.set_ylim(0.5, 1.02)

# Configure legend
ax.legend(fontsize=16, loc="lower right", framealpha=0.95)

# Subtle grid (y-axis only)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
