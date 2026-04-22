""" pyplots.ai
bar-feature-importance: Feature Importance Bar Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Feature importances from a RandomForest model
np.random.seed(42)
features = [
    "Income",
    "Credit Score",
    "Age",
    "Employment Years",
    "Debt Ratio",
    "Number of Accounts",
    "Payment History",
    "Loan Amount",
    "Education Level",
    "Home Ownership",
    "Marital Status",
    "Number of Dependents",
]

# Generate realistic importance values (sorted descending)
importance = np.array([0.182, 0.156, 0.124, 0.098, 0.089, 0.078, 0.072, 0.065, 0.051, 0.042, 0.028, 0.015])
std = np.array([0.025, 0.022, 0.018, 0.015, 0.014, 0.012, 0.011, 0.010, 0.008, 0.007, 0.005, 0.003])

# Sort by importance (highest at top for horizontal bar chart)
sorted_indices = np.argsort(importance)
features_sorted = [features[i] for i in sorted_indices]
importance_sorted = importance[sorted_indices]
std_sorted = std[sorted_indices]

# Create color gradient based on importance values
cmap = plt.cm.Blues
colors = cmap(0.3 + 0.6 * (importance_sorted / importance_sorted.max()))

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

bars = ax.barh(
    features_sorted,
    importance_sorted,
    xerr=std_sorted,
    color=colors,
    edgecolor="#306998",
    linewidth=1.5,
    capsize=5,
    error_kw={"elinewidth": 2, "capthick": 2, "alpha": 0.7},
)

# Add value annotations at the end of bars
for bar, val, err in zip(bars, importance_sorted, std_sorted, strict=True):
    ax.text(
        val + err + 0.008,
        bar.get_y() + bar.get_height() / 2,
        f"{val:.3f}",
        va="center",
        ha="left",
        fontsize=14,
        color="#333333",
    )

# Labels and styling
ax.set_xlabel("Importance Score", fontsize=20)
ax.set_ylabel("Feature", fontsize=20)
ax.set_title("bar-feature-importance · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0, importance_sorted.max() + std_sorted.max() + 0.05)
ax.grid(True, axis="x", alpha=0.3, linestyle="--")

# Add subtle spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
