""" pyplots.ai
residual-plot: Residual Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - housing price prediction example
np.random.seed(42)
n_samples = 150

# Features: house size (sq ft)
house_size = np.random.uniform(800, 3500, n_samples)

# True relationship with some non-linearity to show in residuals
y_true = 50000 + 100 * house_size + 0.02 * house_size**2 + np.random.normal(0, 25000, n_samples)

# Fit linear model using numpy (will show pattern in residuals due to non-linearity)
slope, intercept = np.polyfit(house_size, y_true, 1)
y_pred = slope * house_size + intercept

# Calculate residuals
residuals = y_true - y_pred

# Identify outliers (beyond 2 standard deviations)
residual_std = np.std(residuals)
outlier_mask = np.abs(residuals) > 2 * residual_std

# Create DataFrame for seaborn
df = pd.DataFrame(
    {"Fitted Values": y_pred, "Residuals": residuals, "Type": np.where(outlier_mask, "Outlier (|z| > 2)", "Normal")}
)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot using seaborn scatterplot with hue for outliers
sns.scatterplot(
    data=df,
    x="Fitted Values",
    y="Residuals",
    hue="Type",
    palette={"Normal": "#306998", "Outlier (|z| > 2)": "#FFD43B"},
    s=150,
    alpha=0.7,
    ax=ax,
)

# Add polynomial trend line using seaborn's regplot (order=2 for pattern detection)
sns.regplot(
    data=df,
    x="Fitted Values",
    y="Residuals",
    scatter=False,
    order=2,
    line_kws={"color": "#C44536", "linewidth": 3, "alpha": 0.8, "label": "Trend"},
    ax=ax,
)

# Reference line at y=0
ax.axhline(y=0, color="#333333", linestyle="-", linewidth=2, zorder=1)

# Add ±2 standard deviation bands
ax.axhline(y=2 * residual_std, color="#999999", linestyle="--", linewidth=1.5, alpha=0.7, label="±2 SD")
ax.axhline(y=-2 * residual_std, color="#999999", linestyle="--", linewidth=1.5, alpha=0.7)

# Styling
ax.set_xlabel("Fitted Values (Predicted Price in $)", fontsize=20)
ax.set_ylabel("Residuals (Actual - Predicted)", fontsize=20)
ax.set_title("residual-plot · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=14, loc="upper right", framealpha=0.9)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
