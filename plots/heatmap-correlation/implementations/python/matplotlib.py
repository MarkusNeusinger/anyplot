""" pyplots.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Realistic financial/economic indicators correlation matrix
np.random.seed(42)

# Variable names - economic indicators
variables = [
    "GDP Growth",
    "Inflation",
    "Unemployment",
    "Interest Rate",
    "Stock Index",
    "Consumer Conf.",
    "Industrial Prod.",
    "Trade Balance",
]

n_vars = len(variables)

# Create a realistic correlation matrix with varied relationships
# Including strong negative correlations to demonstrate full colormap range
correlation_matrix = np.eye(n_vars)

# Define realistic correlations between economic indicators
# Includes extreme negative correlations (-0.85 to -0.95 range)
correlations = {
    (0, 4): 0.72,  # GDP Growth - Stock Index (positive)
    (0, 5): 0.68,  # GDP Growth - Consumer Confidence (positive)
    (0, 6): 0.81,  # GDP Growth - Industrial Production (strong positive)
    (0, 2): -0.89,  # GDP Growth - Unemployment (strong negative - Okun's Law)
    (1, 3): 0.58,  # Inflation - Interest Rate (positive)
    (1, 4): -0.42,  # Inflation - Stock Index (negative)
    (2, 5): -0.91,  # Unemployment - Consumer Confidence (strong negative)
    (2, 6): -0.85,  # Unemployment - Industrial Production (strong negative)
    (3, 4): -0.38,  # Interest Rate - Stock Index (negative)
    (4, 5): 0.62,  # Stock Index - Consumer Confidence (positive)
    (4, 6): 0.54,  # Stock Index - Industrial Production (positive)
    (5, 6): 0.77,  # Consumer Confidence - Industrial Production (positive)
    (0, 7): 0.35,  # GDP Growth - Trade Balance (weak positive)
    (1, 7): -0.28,  # Inflation - Trade Balance (weak negative)
    (6, 7): 0.41,  # Industrial Production - Trade Balance (positive)
    (0, 1): -0.22,  # GDP Growth - Inflation (weak negative)
    (0, 3): 0.15,  # GDP Growth - Interest Rate (weak positive)
    (1, 2): 0.32,  # Inflation - Unemployment (Phillips curve inverse)
    (2, 3): 0.25,  # Unemployment - Interest Rate (weak positive)
    (2, 4): -0.78,  # Unemployment - Stock Index (strong negative)
    (3, 5): -0.31,  # Interest Rate - Consumer Confidence (negative)
    (3, 6): -0.19,  # Interest Rate - Industrial Production (weak negative)
    (5, 7): 0.23,  # Consumer Confidence - Trade Balance (weak positive)
    (2, 7): -0.17,  # Unemployment - Trade Balance (weak negative)
    (1, 5): -0.36,  # Inflation - Consumer Confidence (negative)
    (1, 6): -0.29,  # Inflation - Industrial Production (negative)
    (3, 7): 0.11,  # Interest Rate - Trade Balance (weak positive)
    (4, 7): 0.33,  # Stock Index - Trade Balance (positive)
}

# Fill in the correlation matrix (symmetric)
for (i, j), corr in correlations.items():
    correlation_matrix[i, j] = corr
    correlation_matrix[j, i] = corr

# Create mask for upper triangle
mask = np.triu(np.ones_like(correlation_matrix, dtype=bool), k=1)

# Apply mask - set upper triangle to nan for visualization
masked_corr = np.where(mask, np.nan, correlation_matrix)

# Create figure - square format for heatmap
fig, ax = plt.subplots(figsize=(12, 12))

# Create heatmap with diverging colormap centered at zero
im = ax.imshow(masked_corr, cmap="RdBu_r", vmin=-1, vmax=1, aspect="equal")

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.ax.set_ylabel("Correlation Coefficient", fontsize=18, labelpad=15)
cbar.ax.tick_params(labelsize=14)

# Set ticks and labels
ax.set_xticks(np.arange(n_vars))
ax.set_yticks(np.arange(n_vars))
ax.set_xticklabels(variables, fontsize=16, rotation=45, ha="right", rotation_mode="anchor")
ax.set_yticklabels(variables, fontsize=16)

# Add axis labels for explicit context
ax.set_xlabel("Economic Indicators", fontsize=20, labelpad=15)
ax.set_ylabel("Economic Indicators", fontsize=20, labelpad=15)

# Annotate cells with correlation values
for i in range(n_vars):
    for j in range(n_vars):
        if not mask[i, j]:  # Only annotate lower triangle and diagonal
            value = correlation_matrix[i, j]
            # Choose text color based on background
            text_color = "white" if abs(value) > 0.5 else "black"
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", color=text_color, fontsize=14, fontweight="bold")

# Title
ax.set_title("heatmap-correlation · matplotlib · pyplots.ai", fontsize=24, pad=20, fontweight="bold")

# Remove spines
for spine in ax.spines.values():
    spine.set_visible(False)

# Adjust layout
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
