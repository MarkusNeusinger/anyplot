""" pyplots.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Real estate features for correlation analysis
np.random.seed(42)
n_samples = 200

# Generate realistic correlated real estate data
sqft = np.random.normal(2000, 500, n_samples)
bedrooms = np.round(sqft / 600 + np.random.normal(0, 0.5, n_samples)).clip(1, 6)
bathrooms = np.round(bedrooms * 0.7 + np.random.normal(0, 0.3, n_samples)).clip(1, 4)
age = np.random.exponential(20, n_samples).clip(0, 80)
price = sqft * 150 + bedrooms * 15000 - age * 2000 + np.random.normal(0, 30000, n_samples)
garage = np.round(bedrooms * 0.4 + np.random.normal(0, 0.3, n_samples)).clip(0, 3)
lot_size = sqft * 2 + np.random.normal(0, 1000, n_samples)
distance_downtown = np.random.exponential(10, n_samples).clip(1, 40)
crime_rate = distance_downtown * 0.3 + np.random.normal(5, 2, n_samples)

# Create DataFrame with descriptive column names including units
df = pd.DataFrame(
    {
        "Price ($K)": price / 1000,
        "Area (sq ft)": sqft,
        "Bedrooms": bedrooms,
        "Bathrooms": bathrooms,
        "Age (years)": age,
        "Garage Spots": garage,
        "Lot (sq ft)": lot_size,
        "Distance (mi)": distance_downtown,
        "Crime Index": crime_rate,
    }
)

# Compute correlation matrix
corr_matrix = df.corr()

# Create mask for upper triangle
mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)

# Plot - Square format for symmetric matrix
fig, ax = plt.subplots(figsize=(12, 12))

# Create heatmap with seaborn
sns.heatmap(
    corr_matrix,
    mask=mask,
    annot=True,
    fmt=".2f",
    cmap="RdBu_r",
    center=0,
    vmin=-1,
    vmax=1,
    square=True,
    linewidths=0.5,
    linecolor="white",
    cbar_kws={"shrink": 0.8, "label": "Correlation Coefficient"},
    annot_kws={"size": 14},
    ax=ax,
)

# Style
ax.set_title("heatmap-correlation · seaborn · pyplots.ai", fontsize=24, pad=20)
ax.tick_params(axis="both", labelsize=14)

# Rotate labels for readability
plt.xticks(rotation=45, ha="right")
plt.yticks(rotation=0)

# Adjust colorbar label size
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=14)
cbar.ax.set_ylabel("Correlation Coefficient", fontsize=16)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
