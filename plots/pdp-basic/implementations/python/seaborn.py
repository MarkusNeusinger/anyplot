""" pyplots.ai
pdp-basic: Partial Dependence Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Set seed for reproducibility
np.random.seed(42)

# Generate synthetic regression data (housing price prediction scenario)
X, y = make_regression(n_samples=500, n_features=5, noise=10, random_state=42)

# Feature names for context
feature_names = ["Square Feet", "Bedrooms", "Age (years)", "Distance to City", "Lot Size"]

# Train a gradient boosting model
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, y)

# Compute partial dependence for feature 0 (Square Feet)
feature_idx = 0
pd_result = partial_dependence(model, X, features=[feature_idx], kind="average", grid_resolution=80)

# Extract values
feature_values = pd_result["grid_values"][0]
pd_values = pd_result["average"][0]

# Center partial dependence at zero for easier interpretation
pd_values_centered = pd_values - pd_values.mean()

# Compute confidence interval using individual predictions (approximation)
pd_individual = partial_dependence(model, X, features=[feature_idx], kind="individual", grid_resolution=80)
ice_lines = pd_individual["individual"][0]  # Shape: (n_samples, n_grid_points)
ice_centered = ice_lines - ice_lines.mean(axis=1, keepdims=True)
std_dev = np.std(ice_centered, axis=0)
ci_lower = pd_values_centered - 1.96 * std_dev / np.sqrt(len(X))
ci_upper = pd_values_centered + 1.96 * std_dev / np.sqrt(len(X))

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot confidence band
ax.fill_between(feature_values, ci_lower, ci_upper, alpha=0.3, color="#306998", label="95% Confidence Interval")

# Plot main PDP line using seaborn lineplot
sns.lineplot(x=feature_values, y=pd_values_centered, ax=ax, color="#306998", linewidth=3, label="Partial Dependence")

# Add rug plot to show data distribution
# Sample of actual feature values for rug
feature_data = X[:, feature_idx]
sns.rugplot(x=feature_data, ax=ax, color="#FFD43B", height=0.03, alpha=0.6)

# Add horizontal line at zero
ax.axhline(y=0, color="gray", linestyle="--", linewidth=1.5, alpha=0.5)

# Styling
ax.set_xlabel(f"{feature_names[feature_idx]} (standardized)", fontsize=20)
ax.set_ylabel("Partial Dependence (centered)", fontsize=20)
ax.set_title("pdp-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
