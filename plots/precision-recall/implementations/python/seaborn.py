""" anyplot.ai
precision-recall: Precision-Recall Curve
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-10
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np


# Remove local directory from path to avoid shadowing library imports
sys.path = [p for p in sys.path if not p.endswith("/python")]  # noqa: E402

import seaborn as sns  # noqa: E402
from sklearn.metrics import average_precision_score, precision_recall_curve  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

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

# Data - Simulate binary classification with imbalanced classes (fraud detection scenario)
np.random.seed(42)
n_samples = 1000
n_positive = 100  # 10% positive class (imbalanced)

# Ground truth labels
y_true = np.zeros(n_samples)
y_true[:n_positive] = 1
np.random.shuffle(y_true)

# Simulate classifier scores - better separation for positives
y_scores_good = np.where(
    y_true == 1,
    np.random.beta(5, 2, n_samples),  # Positives: higher scores
    np.random.beta(2, 5, n_samples),  # Negatives: lower scores
)

y_scores_moderate = np.where(
    y_true == 1,
    np.random.beta(3, 2, n_samples),  # Positives: moderately higher
    np.random.beta(2, 3, n_samples),  # Negatives: moderately lower
)

y_scores_poor = np.where(
    y_true == 1,
    np.random.beta(2, 2, n_samples),  # Positives: similar to negatives
    np.random.beta(2, 2, n_samples),  # Negatives: similar to positives
)

# Calculate precision-recall curves
precision_good, recall_good, _ = precision_recall_curve(y_true, y_scores_good)
precision_moderate, recall_moderate, _ = precision_recall_curve(y_true, y_scores_moderate)
precision_poor, recall_poor, _ = precision_recall_curve(y_true, y_scores_poor)

# Average precision scores
ap_good = average_precision_score(y_true, y_scores_good)
ap_moderate = average_precision_score(y_true, y_scores_moderate)
ap_poor = average_precision_score(y_true, y_scores_poor)

# Baseline (random classifier)
baseline = n_positive / n_samples

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot PR curves using seaborn's lineplot style with step interpolation
# Good classifier
ax.step(
    recall_good, precision_good, where="post", linewidth=3, color=IMPRINT[0], label=f"Model A (AP = {ap_good:.2f})"
)
ax.fill_between(recall_good, precision_good, step="post", alpha=0.2, color=IMPRINT[0])

# Moderate classifier
ax.step(
    recall_moderate,
    precision_moderate,
    where="post",
    linewidth=3,
    color=IMPRINT[1],
    label=f"Model B (AP = {ap_moderate:.2f})",
)
ax.fill_between(recall_moderate, precision_moderate, step="post", alpha=0.2, color=IMPRINT[1])

# Poor classifier
ax.step(
    recall_poor, precision_poor, where="post", linewidth=3, color=IMPRINT[2], label=f"Model C (AP = {ap_poor:.2f})"
)
ax.fill_between(recall_poor, precision_poor, step="post", alpha=0.2, color=IMPRINT[2])

# Baseline reference line
ax.axhline(y=baseline, linestyle="--", linewidth=2, color=INK_SOFT, label=f"Random Classifier (P = {baseline:.2f})")

# Styling with seaborn aesthetics
ax.set_xlabel("Recall (Sensitivity)", fontsize=20)
ax.set_ylabel("Precision (Positive Predictive Value)", fontsize=20)
ax.set_title("precision-recall · seaborn · anyplot.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set axis limits
ax.set_xlim([0.0, 1.0])
ax.set_ylim([0.0, 1.05])

# Legend
ax.legend(loc="upper right", fontsize=16, frameon=True, fancybox=True, framealpha=0.9)

# Grid styling
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
