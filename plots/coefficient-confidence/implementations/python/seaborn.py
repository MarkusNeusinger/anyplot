""" pyplots.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Regression coefficients from a housing price prediction model
np.random.seed(42)

variables = [
    "Square Footage",
    "Number of Bedrooms",
    "Number of Bathrooms",
    "Lot Size (acres)",
    "Age of Home (years)",
    "Distance to Downtown",
    "School Rating",
    "Crime Rate Index",
    "Garage Spaces",
    "Has Pool",
    "Renovated Recently",
    "Neighborhood Tier",
]

# Generate realistic regression coefficients
coefficients = [0.45, 0.12, 0.18, 0.08, -0.15, -0.22, 0.25, -0.31, 0.09, 0.14, 0.11, 0.28]

# Generate confidence intervals (wider for less certain estimates)
ci_widths = [0.08, 0.15, 0.12, 0.18, 0.09, 0.14, 0.11, 0.16, 0.20, 0.13, 0.22, 0.10]
ci_lower = [c - w for c, w in zip(coefficients, ci_widths, strict=True)]
ci_upper = [c + w for c, w in zip(coefficients, ci_widths, strict=True)]

# Determine significance (CI does not cross zero)
significant = [not (low <= 0 <= high) for low, high in zip(ci_lower, ci_upper, strict=True)]

# Create DataFrame
df = pd.DataFrame(
    {
        "variable": variables,
        "coefficient": coefficients,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "significant": significant,
    }
)

# Sort by coefficient magnitude for easier comparison
df = df.sort_values("coefficient", ascending=True).reset_index(drop=True)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Define colors based on significance
colors = ["#306998" if sig else "#808080" for sig in df["significant"]]

# Plot using seaborn pointplot style with custom error bars
y_positions = np.arange(len(df))

# Plot error bars (confidence intervals)
for i, row in df.iterrows():
    color = "#306998" if row["significant"] else "#808080"
    ax.hlines(y=i, xmin=row["ci_lower"], xmax=row["ci_upper"], color=color, linewidth=3, alpha=0.7)

# Plot coefficient points using seaborn scatterplot
scatter_df = df.copy()
scatter_df["y_pos"] = y_positions

sns.scatterplot(
    data=scatter_df,
    x="coefficient",
    y="y_pos",
    hue="significant",
    palette={True: "#306998", False: "#808080"},
    s=400,
    ax=ax,
    legend=True,
    zorder=5,
)

# Add vertical reference line at zero
ax.axvline(x=0, color="#FFD43B", linewidth=3, linestyle="--", alpha=0.9, zorder=1)

# Set y-axis labels to variable names
ax.set_yticks(y_positions)
ax.set_yticklabels(df["variable"], fontsize=16)

# Styling
ax.set_xlabel("Coefficient Estimate (Standardized)", fontsize=20)
ax.set_ylabel("Predictor Variable", fontsize=20)
ax.set_title("coefficient-confidence · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="x", labelsize=16)
ax.grid(True, axis="x", alpha=0.3, linestyle="--")

# Update legend with correct label order
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, ["Not Significant", "Significant (p < 0.05)"], fontsize=14, loc="lower right", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
