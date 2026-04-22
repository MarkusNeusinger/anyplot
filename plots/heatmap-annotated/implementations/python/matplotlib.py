""" pyplots.ai
heatmap-annotated: Annotated Heatmap
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Correlation matrix for financial metrics
np.random.seed(42)
variables = ["Revenue", "Profit", "Expenses", "Growth", "Risk", "ROI", "Debt", "Assets"]
n = len(variables)

# Generate a realistic correlation matrix (symmetric, diagonal = 1)
base = np.random.randn(n, n) * 0.3
correlation = (base + base.T) / 2  # Make symmetric
np.fill_diagonal(correlation, 1.0)  # Diagonal = 1
correlation = np.clip(correlation, -1, 1)  # Ensure valid correlation range

# Add some realistic correlations
correlation[0, 1] = correlation[1, 0] = 0.85  # Revenue-Profit: strong positive
correlation[0, 2] = correlation[2, 0] = 0.72  # Revenue-Expenses: positive
correlation[1, 2] = correlation[2, 1] = -0.45  # Profit-Expenses: negative
correlation[3, 5] = correlation[5, 3] = 0.78  # Growth-ROI: strong positive
correlation[4, 6] = correlation[6, 4] = 0.65  # Risk-Debt: positive
correlation[1, 5] = correlation[5, 1] = 0.82  # Profit-ROI: strong positive

# Create plot (square format for heatmap)
fig, ax = plt.subplots(figsize=(12, 12))

# Create heatmap with diverging colormap
im = ax.imshow(correlation, cmap="RdBu_r", vmin=-1, vmax=1, aspect="equal")

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax, shrink=0.8, aspect=30)
cbar.ax.tick_params(labelsize=16)
cbar.set_label("Correlation Coefficient", fontsize=18, labelpad=15)

# Set ticks and labels
ax.set_xticks(np.arange(n))
ax.set_yticks(np.arange(n))
ax.set_xticklabels(variables, fontsize=16)
ax.set_yticklabels(variables, fontsize=16)

# Rotate x-axis labels for better readability
plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

# Add text annotations in each cell
for i in range(n):
    for j in range(n):
        value = correlation[i, j]
        # Choose text color based on background intensity
        text_color = "white" if abs(value) > 0.5 else "black"
        ax.text(j, i, f"{value:.2f}", ha="center", va="center", color=text_color, fontsize=14, fontweight="bold")

# Styling
ax.set_title("heatmap-annotated · matplotlib · pyplots.ai", fontsize=24, pad=20)
ax.set_xlabel("Variables", fontsize=20, labelpad=15)
ax.set_ylabel("Variables", fontsize=20, labelpad=15)

# Add subtle grid between cells
ax.set_xticks(np.arange(n + 1) - 0.5, minor=True)
ax.set_yticks(np.arange(n + 1) - 0.5, minor=True)
ax.grid(which="minor", color="white", linestyle="-", linewidth=2)
ax.tick_params(which="minor", bottom=False, left=False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
