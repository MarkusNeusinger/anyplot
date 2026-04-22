""" pyplots.ai
pdp-basic: Partial Dependence Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Data: Train a gradient boosting model and compute partial dependence
np.random.seed(42)
X, y = make_regression(n_samples=500, n_features=5, noise=15, random_state=42)

# Train model
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, y)

# Compute partial dependence for feature 0
feature_idx = 0

# Get partial dependence using sklearn
pd_result = partial_dependence(model, X, features=[feature_idx], kind="both", grid_resolution=80)
pdp_values = pd_result["average"][0]
ice_lines = pd_result["individual"][0]
grid_values = pd_result["grid_values"][0]

# Calculate confidence interval (mean ± std of ICE lines)
ice_mean = pdp_values
ice_std = np.std(ice_lines, axis=0)

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9))

# Plot ICE lines (faint individual lines)
for i in range(0, len(ice_lines), 10):  # Sample every 10th line for clarity
    ax.plot(grid_values, ice_lines[i], color="#306998", alpha=0.1, linewidth=1)

# Plot confidence band
ax.fill_between(
    grid_values,
    ice_mean - 1.96 * ice_std,
    ice_mean + 1.96 * ice_std,
    alpha=0.25,
    color="#306998",
    label="95% Confidence Interval",
)

# Plot main PDP line
ax.plot(grid_values, pdp_values, color="#306998", linewidth=4, label="Partial Dependence")

# Add rug plot showing data distribution
rug_y = ax.get_ylim()[0]
ax.scatter(
    X[:, feature_idx], np.full(len(X), rug_y), marker="|", color="#FFD43B", alpha=0.4, s=100, label="Data Distribution"
)

# Labels and styling
ax.set_xlabel("Feature Value", fontsize=20)
ax.set_ylabel("Partial Dependence (Predicted Value)", fontsize=20)
ax.set_title("pdp-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
