""" anyplot.ai
pdp-basic: Partial Dependence Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-15
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

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

# Compute confidence interval using individual predictions
pd_individual = partial_dependence(model, X, features=[feature_idx], kind="individual", grid_resolution=80)
ice_lines = pd_individual["individual"][0]
ice_centered = ice_lines - ice_lines.mean(axis=1, keepdims=True)
std_dev = np.std(ice_centered, axis=0)
ci_lower = pd_values_centered - 1.96 * std_dev / np.sqrt(len(X))
ci_upper = pd_values_centered + 1.96 * std_dev / np.sqrt(len(X))

# Create figure with seaborn style
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
    },
)

fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Plot confidence band
ax.fill_between(feature_values, ci_lower, ci_upper, alpha=0.25, color=BRAND, label="95% Confidence Interval")

# Plot main PDP line using seaborn
sns.lineplot(
    x=feature_values, y=pd_values_centered, ax=ax, color=BRAND, linewidth=3, label="Partial Dependence", legend=False
)

# Add rug plot to show data distribution
feature_data = X[:, feature_idx]
sns.rugplot(x=feature_data, ax=ax, color=INK_SOFT, height=0.03, alpha=0.5)

# Add horizontal line at zero for reference
ax.axhline(y=0, color=INK_SOFT, linestyle="--", linewidth=1.5, alpha=0.4)

# Styling
ax.set_xlabel(f"{feature_names[feature_idx]}", fontsize=20, color=INK)
ax.set_ylabel("Partial Dependence (centered)", fontsize=20, color=INK)
ax.set_title("pdp-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Subtle grid
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Legend
handles, labels = ax.get_legend_handles_labels()
ax.legend(
    handles,
    labels,
    fontsize=16,
    loc="upper left",
    frameon=True,
    fancybox=False,
    edgecolor=INK_SOFT,
    facecolor=ELEVATED_BG,
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
