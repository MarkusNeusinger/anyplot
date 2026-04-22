""" pyplots.ai
learning-curve-basic: Model Learning Curve
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Simulate learning curve for a model showing slight overfitting pattern
np.random.seed(42)

# Training set sizes (10 different sizes)
train_sizes = np.array([50, 100, 200, 400, 600, 800, 1000, 1200, 1400, 1600])

# Simulate 5 cross-validation folds
n_folds = 5
n_sizes = len(train_sizes)

# Training scores: Start high, stay high (model fits training data well)
train_scores_mean = 0.99 - 0.15 * np.exp(-train_sizes / 200)
train_scores = np.zeros((n_folds, n_sizes))
for i in range(n_folds):
    noise = np.random.randn(n_sizes) * 0.01
    train_scores[i] = train_scores_mean + noise

# Validation scores: Start lower, improve with more data (learning effect)
# Show a gap with training that narrows as data increases
validation_scores_mean = 0.65 + 0.20 * (1 - np.exp(-train_sizes / 500))
validation_scores = np.zeros((n_folds, n_sizes))
for i in range(n_folds):
    noise = np.random.randn(n_sizes) * 0.02
    validation_scores[i] = validation_scores_mean + noise

# Calculate means and standard deviations
train_mean = np.mean(train_scores, axis=0)
train_std = np.std(train_scores, axis=0)
val_mean = np.mean(validation_scores, axis=0)
val_std = np.std(validation_scores, axis=0)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Training curve with confidence band
ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.2, color="#306998")
ax.plot(train_sizes, train_mean, "o-", color="#306998", linewidth=3, markersize=10, label="Training Score")

# Validation curve with confidence band
ax.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.2, color="#FFD43B")
ax.plot(train_sizes, val_mean, "s-", color="#FFD43B", linewidth=3, markersize=10, label="Validation Score")

# Labels and styling
ax.set_xlabel("Training Set Size (samples)", fontsize=20)
ax.set_ylabel("Accuracy Score", fontsize=20)
ax.set_title("learning-curve-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="lower right")
ax.grid(True, alpha=0.3, linestyle="--")

# Set y-axis limits to show full range with some padding
ax.set_ylim(0.55, 1.02)
ax.set_xlim(0, 1700)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
