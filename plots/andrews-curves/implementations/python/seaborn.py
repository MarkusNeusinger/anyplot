""" pyplots.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Load iris dataset from seaborn
df = sns.load_dataset("iris")

# Normalize variables to similar scales
features = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
for col in features:
    df[col + "_norm"] = (df[col] - df[col].mean()) / df[col].std()

norm_features = [f + "_norm" for f in features]

# Generate t values from -pi to pi
t = np.linspace(-np.pi, np.pi, 200)

# Compute Andrews curves for all observations
# Andrews curve: f(t) = x1/sqrt(2) + x2*sin(t) + x3*cos(t) + x4*sin(2t) + ...
curves_data = []
for idx, row in df.iterrows():
    values = row[norm_features].values.astype(float)
    # Compute Fourier series for this observation
    curve_vals = np.full_like(t, values[0] / np.sqrt(2))
    for i in range(1, len(values)):
        if i % 2 == 1:
            curve_vals = curve_vals + values[i] * np.sin((i + 1) // 2 * t)
        else:
            curve_vals = curve_vals + values[i] * np.cos(i // 2 * t)

    for t_val, y_val in zip(t, curve_vals, strict=True):
        curves_data.append({"t": t_val, "f(t)": y_val, "species": row["species"], "obs_id": idx})

curves_df = pd.DataFrame(curves_data)

# Color palette using Python Blue, Yellow, and a third color
colors = {"setosa": "#306998", "versicolor": "#FFD43B", "virginica": "#E74C3C"}

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Plot Andrews curves using lineplot with grouped data
sns.lineplot(
    data=curves_df,
    x="t",
    y="f(t)",
    hue="species",
    palette=colors,
    alpha=0.4,
    linewidth=1.5,
    units="obs_id",
    estimator=None,
    ax=ax,
)

# Style the plot
ax.set_xlabel("t", fontsize=20)
ax.set_ylabel("f(t)", fontsize=20)
ax.set_title("andrews-curves · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set x-axis ticks to show pi values
ax.set_xticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
ax.set_xticklabels(["-π", "-π/2", "0", "π/2", "π"], fontsize=16)

# Customize legend
ax.legend(title="Species", fontsize=16, title_fontsize=18, loc="upper right")

# Subtle grid
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
