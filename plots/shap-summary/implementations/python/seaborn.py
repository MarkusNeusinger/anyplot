""" pyplots.ai
shap-summary: SHAP Summary Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import Normalize
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import GradientBoostingClassifier


# Data - Train a model and compute SHAP-like values
np.random.seed(42)
data = load_breast_cancer()
X = data.data[:, :12]  # Use first 12 features for cleaner visualization
feature_names = list(data.feature_names[:12])

# Train a gradient boosting model
model = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, data.target)

# Compute approximate SHAP values using tree-based contribution approach
n_samples = 200
sample_indices = np.random.choice(len(X), n_samples, replace=False)
X_sample = X[sample_indices]

# Calculate feature contributions with better spread
base_pred = model.predict_proba(X_sample)[:, 1]
baseline = base_pred.mean()
shap_values = np.zeros((n_samples, X_sample.shape[1]))

for i in range(X_sample.shape[1]):
    # Create more varied perturbations for better SHAP value distribution
    X_low = X_sample.copy()
    X_high = X_sample.copy()
    X_low[:, i] = np.percentile(X_sample[:, i], 10)
    X_high[:, i] = np.percentile(X_sample[:, i], 90)
    pred_low = model.predict_proba(X_low)[:, 1]
    pred_high = model.predict_proba(X_high)[:, 1]
    # Compute contribution based on feature value position
    feat_normalized = (X_sample[:, i] - X_sample[:, i].min()) / (X_sample[:, i].max() - X_sample[:, i].min() + 1e-8)
    shap_values[:, i] = (pred_high - pred_low) * (feat_normalized - 0.5) * 2

# Normalize feature values for coloring (0 to 1 scale)
feature_values_norm = (X_sample - X_sample.min(axis=0)) / (X_sample.max(axis=0) - X_sample.min(axis=0) + 1e-8)

# Sort features by mean absolute SHAP value
mean_abs_shap = np.abs(shap_values).mean(axis=0)
sorted_indices = np.argsort(mean_abs_shap)[::-1][:10]  # Top 10 features

# Prepare data for seaborn stripplot
plot_data = []
for rank, feat_idx in enumerate(sorted_indices):
    for sample in range(n_samples):
        plot_data.append(
            {
                "Feature": feature_names[feat_idx],
                "SHAP Value": shap_values[sample, feat_idx],
                "Feature Value": feature_values_norm[sample, feat_idx],
                "Rank": rank,
            }
        )

df = pd.DataFrame(plot_data)

# Create ordered category for proper feature ordering
ordered_features = [feature_names[i] for i in sorted_indices]
df["Feature"] = pd.Categorical(df["Feature"], categories=ordered_features, ordered=True)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn stripplot for the main visualization
sns.stripplot(
    data=df,
    x="SHAP Value",
    y="Feature",
    hue="Feature Value",
    palette="coolwarm",
    size=8,
    alpha=0.7,
    jitter=0.3,
    legend=False,
    ax=ax,
)

# Add vertical line at x=0
ax.axvline(x=0, color="#306998", linestyle="-", linewidth=2, alpha=0.8)

# Styling
ax.set_xlabel("SHAP Value (Impact on Model Output)", fontsize=20)
ax.set_ylabel("Feature", fontsize=20)
ax.set_title("shap-summary · seaborn · pyplots.ai", fontsize=24, pad=20)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, axis="x", alpha=0.3, linestyle="--")

# Add colorbar for feature values
sm = plt.cm.ScalarMappable(cmap="coolwarm", norm=Normalize(vmin=0, vmax=1))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.02)
cbar.set_label("Feature Value (Low to High)", fontsize=16, rotation=270, labelpad=20)
cbar.ax.tick_params(labelsize=14)

# Adjust spines using seaborn
sns.despine(left=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
