""" pyplots.ai
precision-recall: Precision-Recall Curve
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np


# Generate synthetic classification data with imbalanced classes
np.random.seed(42)
n_samples = 500

# Simulate imbalanced dataset: 20% positive, 80% negative
positive_ratio = 0.2
n_positive = int(n_samples * positive_ratio)
n_negative = n_samples - n_positive

# True labels
y_true = np.concatenate([np.ones(n_positive), np.zeros(n_negative)])

# Simulate classifier scores - good classifier gives higher scores to positives
positive_scores = np.random.beta(5, 2, n_positive)  # Skewed higher
negative_scores = np.random.beta(2, 5, n_negative)  # Skewed lower
y_scores = np.concatenate([positive_scores, negative_scores])

# Calculate precision-recall curve
# Sort by scores descending
desc_score_indices = np.argsort(y_scores)[::-1]
y_scores_sorted = y_scores[desc_score_indices]
y_true_sorted = y_true[desc_score_indices]

# Get unique thresholds
distinct_value_indices = np.where(np.diff(y_scores_sorted))[0]
threshold_idxs = np.concatenate([[0], distinct_value_indices + 1])

# Calculate TP, FP cumulative sums
tps = np.cumsum(y_true_sorted)
fps = np.cumsum(1 - y_true_sorted)

# Calculate precision and recall at each threshold
precision_vals = tps / (tps + fps)
recall_vals = tps / tps[-1]

# Use thresholds at distinct values (add starting point: recall=0, precision=1)
precision = np.concatenate([[1], precision_vals[threshold_idxs]])
recall = np.concatenate([[0], recall_vals[threshold_idxs]])

# Calculate Average Precision (area under curve)
recall_diff = np.diff(recall)
average_precision = np.sum(precision[1:] * recall_diff)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot precision-recall curve with stepped line style
ax.step(
    recall, precision, where="post", color="#306998", linewidth=3, label=f"Classifier (AP = {average_precision:.3f})"
)

# Fill area under curve for visual emphasis
ax.fill_between(recall, precision, step="post", alpha=0.2, color="#306998")

# Baseline: random classifier (horizontal line at positive class ratio)
ax.axhline(
    y=positive_ratio,
    color="#FFD43B",
    linestyle="--",
    linewidth=2.5,
    label=f"Random Baseline (P = {positive_ratio:.0%})",
)

# Iso-F1 curves
f1_scores = np.linspace(0.2, 0.8, num=4)
for f1_score in f1_scores:
    x = np.linspace(0.01, 1, 100)
    y = f1_score * x / (2 * x - f1_score)
    mask = (y >= 0) & (y <= 1) & (x >= f1_score / 2)
    ax.plot(x[mask], y[mask], color="gray", alpha=0.3, linewidth=1.5, linestyle=":")
    # Add F1 label at end of curve
    if np.any(mask):
        label_x = x[mask][-1]
        label_y = y[mask][-1]
        ax.annotate(
            f"F1={f1_score:.1f}", xy=(label_x, label_y), fontsize=12, color="gray", alpha=0.7, ha="left", va="bottom"
        )

# Styling
ax.set_xlabel("Recall", fontsize=20)
ax.set_ylabel("Precision", fontsize=20)
ax.set_title("precision-recall · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim([0.0, 1.0])
ax.set_ylim([0.0, 1.05])
ax.legend(loc="upper right", fontsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
