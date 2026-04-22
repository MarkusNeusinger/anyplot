""" pyplots.ai
precision-recall: Precision-Recall Curve
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import average_precision_score, precision_recall_curve


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

# Calculate precision-recall curves
precision_good, recall_good, _ = precision_recall_curve(y_true, y_scores_good)
precision_moderate, recall_moderate, _ = precision_recall_curve(y_true, y_scores_moderate)

# Average precision scores
ap_good = average_precision_score(y_true, y_scores_good)
ap_moderate = average_precision_score(y_true, y_scores_moderate)

# Baseline (random classifier)
baseline = n_positive / n_samples

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Plot PR curves using seaborn's lineplot style with step interpolation
# Good classifier
ax.step(recall_good, precision_good, where="post", linewidth=3, color="#306998", label=f"Model A (AP = {ap_good:.2f})")
ax.fill_between(recall_good, precision_good, step="post", alpha=0.2, color="#306998")

# Moderate classifier
ax.step(
    recall_moderate,
    precision_moderate,
    where="post",
    linewidth=3,
    color="#FFD43B",
    label=f"Model B (AP = {ap_moderate:.2f})",
)
ax.fill_between(recall_moderate, precision_moderate, step="post", alpha=0.2, color="#FFD43B")

# Baseline reference line
ax.axhline(y=baseline, linestyle="--", linewidth=2, color="#888888", label=f"Random Classifier (P = {baseline:.2f})")

# Styling with seaborn aesthetics
ax.set_xlabel("Recall (Sensitivity)", fontsize=20)
ax.set_ylabel("Precision (Positive Predictive Value)", fontsize=20)
ax.set_title("precision-recall · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set axis limits
ax.set_xlim([0.0, 1.0])
ax.set_ylim([0.0, 1.05])

# Legend
ax.legend(loc="upper right", fontsize=16, frameon=True, fancybox=True, framealpha=0.9, edgecolor="#cccccc")

# Grid styling
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
