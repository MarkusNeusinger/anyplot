""" pyplots.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.datasets import load_wine
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance


# Data - Using wine dataset with permutation importance from Random Forest
wine = load_wine()
X, y = wine.data, wine.target
feature_names = wine.feature_names

# Train a Random Forest model
np.random.seed(42)
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X, y)

# Calculate permutation importance
perm_importance = permutation_importance(clf, X, y, n_repeats=10, random_state=42)

# Extract importance values
importance_mean = perm_importance.importances_mean
importance_std = perm_importance.importances_std

# Sort by importance (descending)
sorted_idx = np.argsort(importance_mean)[::-1]
sorted_features = [feature_names[i] for i in sorted_idx]
sorted_mean = importance_mean[sorted_idx]
sorted_std = importance_std[sorted_idx]

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Color palette based on importance values (sequential)
colors = sns.color_palette("viridis", n_colors=len(sorted_features))
# Map colors to sorted importance (highest importance = darkest)
color_order = list(reversed(colors))

# Create horizontal bar plot with seaborn
y_positions = np.arange(len(sorted_features))
sns.barplot(x=sorted_mean, y=sorted_features, hue=sorted_features, palette=color_order, legend=False, ax=ax, orient="h")

# Add error bars manually (seaborn barplot doesn't support horizontal error bars directly)
ax.errorbar(
    sorted_mean, y_positions, xerr=sorted_std, fmt="none", ecolor="#333333", elinewidth=2, capsize=5, capthick=2
)

# Add vertical reference line at x=0
ax.axvline(x=0, color="#333333", linestyle="-", linewidth=1.5, alpha=0.7)

# Styling
ax.set_xlabel("Mean Importance (Decrease in Accuracy)", fontsize=20)
ax.set_ylabel("Feature", fontsize=20)
ax.set_title("bar-permutation-importance · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, axis="x", alpha=0.3, linestyle="--")

# Adjust layout
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
