""" pyplots.ai
shap-summary: SHAP Summary Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


# Data - Simulating SHAP values from a house price prediction model
np.random.seed(42)
n_samples = 300
n_features = 12

# Feature names (house price prediction context)
feature_names = [
    "Square Footage",
    "Number of Bedrooms",
    "Age of House (years)",
    "Distance to City (km)",
    "Number of Bathrooms",
    "Garage Size",
    "Lot Size (acres)",
    "School Rating",
    "Crime Rate Index",
    "Year Renovated",
    "Property Tax Rate",
    "Median Income (area)",
]

# Generate feature values (normalized 0-1 for coloring)
feature_values = np.random.rand(n_samples, n_features)

# Generate SHAP values with realistic patterns
# More important features have larger absolute SHAP values
importance_scale = np.array([2.5, 1.8, 1.5, 1.4, 1.2, 1.0, 0.9, 0.8, 0.7, 0.5, 0.4, 0.3])
shap_values = np.zeros((n_samples, n_features))

for i in range(n_features):
    # Create SHAP values with some correlation to feature values
    # Higher feature values generally -> higher SHAP values (but not always)
    base_shap = (feature_values[:, i] - 0.5) * importance_scale[i]
    noise = np.random.randn(n_samples) * importance_scale[i] * 0.3
    shap_values[:, i] = base_shap + noise

# Sort features by mean absolute SHAP value (most important first)
mean_abs_shap = np.abs(shap_values).mean(axis=0)
sorted_indices = np.argsort(mean_abs_shap)[::-1]

# Take top 10 features for clarity
top_n = 10
sorted_indices = sorted_indices[:top_n]
sorted_feature_names = [feature_names[i] for i in sorted_indices]
sorted_shap_values = shap_values[:, sorted_indices]
sorted_feature_values = feature_values[:, sorted_indices]

# Create custom blue-to-red colormap
colors = ["#306998", "#a0a0a0", "#d62728"]  # Python Blue -> Gray -> Red
cmap = LinearSegmentedColormap.from_list("shap_cmap", colors, N=256)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot each feature as a row of scattered points
for i in range(top_n):
    feature_idx = top_n - 1 - i  # Reverse so most important is at top
    shap_vals = sorted_shap_values[:, feature_idx]
    feat_vals = sorted_feature_values[:, feature_idx]

    # Add jitter to y-position to reduce overlap
    y_positions = np.ones(n_samples) * i + np.random.uniform(-0.2, 0.2, n_samples)

    # Scatter plot with color based on feature value
    scatter = ax.scatter(
        shap_vals, y_positions, c=feat_vals, cmap=cmap, s=80, alpha=0.7, edgecolors="none", vmin=0, vmax=1
    )

# Vertical line at x=0
ax.axvline(x=0, color="#333333", linewidth=2, linestyle="-", alpha=0.7)

# Styling
ax.set_yticks(range(top_n))
ax.set_yticklabels(sorted_feature_names[::-1], fontsize=16)
ax.set_xlabel("SHAP Value (Impact on Model Output)", fontsize=20)
ax.set_title("shap-summary · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="x", labelsize=16)

# Grid (subtle, only vertical)
ax.grid(True, axis="x", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Add colorbar
cbar = plt.colorbar(scatter, ax=ax, shrink=0.8, aspect=30, pad=0.02)
cbar.set_label("Feature Value", fontsize=18)
cbar.set_ticks([0, 1])
cbar.set_ticklabels(["Low", "High"])
cbar.ax.tick_params(labelsize=14)

# Adjust layout
ax.set_xlim(ax.get_xlim()[0] * 1.1, ax.get_xlim()[1] * 1.1)
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
