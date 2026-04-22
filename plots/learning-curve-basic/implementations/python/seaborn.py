""" pyplots.ai
learning-curve-basic: Model Learning Curve
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


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

# Plot setup
sns.set_context("talk", font_scale=1.1)
sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(16, 9))

# Define colors - Python Blue for training, Python Yellow for validation
train_color = "#306998"
val_color = "#FFD43B"

# Plot training curve with confidence band
ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.2, color=train_color)
sns.lineplot(
    x=train_sizes,
    y=train_mean,
    ax=ax,
    color=train_color,
    linewidth=3,
    marker="o",
    markersize=10,
    label="Training Score",
)

# Plot validation curve with confidence band
ax.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.2, color=val_color)
sns.lineplot(
    x=train_sizes, y=val_mean, ax=ax, color=val_color, linewidth=3, marker="s", markersize=10, label="Validation Score"
)

# Labels and styling
ax.set_xlabel("Training Set Size", fontsize=20)
ax.set_ylabel("Accuracy Score", fontsize=20)
ax.set_title("learning-curve-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set y-axis limits for better visualization
ax.set_ylim(0.5, 1.02)

# Configure legend
ax.legend(fontsize=16, loc="lower right", framealpha=0.9)

# Subtle grid
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
