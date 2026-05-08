"""pyplots.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme configuration
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data - Realistic weather variables correlation matrix
np.random.seed(42)

# Variable names - weather metrics
variables = [
    "Temperature",
    "Humidity",
    "Wind Speed",
    "Precipitation",
    "Air Pressure",
    "Solar Radiation",
    "UV Index",
    "Cloud Cover",
]

n_vars = len(variables)

# Create a realistic correlation matrix with varied relationships
correlation_matrix = np.eye(n_vars)

# Define realistic correlations between weather variables
correlations = {
    (0, 1): -0.82,  # Temperature - Humidity (strong negative)
    (0, 2): 0.15,  # Temperature - Wind Speed (weak positive)
    (0, 3): -0.48,  # Temperature - Precipitation (negative)
    (0, 4): -0.71,  # Temperature - Air Pressure (strong negative)
    (0, 5): 0.88,  # Temperature - Solar Radiation (strong positive)
    (0, 6): 0.79,  # Temperature - UV Index (strong positive)
    (0, 7): -0.65,  # Temperature - Cloud Cover (negative)
    (1, 2): 0.35,  # Humidity - Wind Speed (weak positive)
    (1, 3): 0.72,  # Humidity - Precipitation (strong positive)
    (1, 4): 0.58,  # Humidity - Air Pressure (positive)
    (1, 5): -0.84,  # Humidity - Solar Radiation (strong negative)
    (1, 6): -0.76,  # Humidity - UV Index (strong negative)
    (1, 7): 0.81,  # Humidity - Cloud Cover (strong positive)
    (2, 3): 0.42,  # Wind Speed - Precipitation (positive)
    (2, 4): -0.31,  # Wind Speed - Air Pressure (weak negative)
    (2, 5): 0.09,  # Wind Speed - Solar Radiation (very weak)
    (2, 6): -0.12,  # Wind Speed - UV Index (very weak negative)
    (2, 7): 0.38,  # Wind Speed - Cloud Cover (weak positive)
    (3, 4): -0.52,  # Precipitation - Air Pressure (negative)
    (3, 5): -0.68,  # Precipitation - Solar Radiation (strong negative)
    (3, 6): -0.61,  # Precipitation - UV Index (strong negative)
    (3, 7): 0.74,  # Precipitation - Cloud Cover (strong positive)
    (4, 5): 0.45,  # Air Pressure - Solar Radiation (positive)
    (4, 6): 0.39,  # Air Pressure - UV Index (positive)
    (4, 7): -0.43,  # Air Pressure - Cloud Cover (negative)
    (5, 6): 0.85,  # Solar Radiation - UV Index (strong positive)
    (5, 7): -0.79,  # Solar Radiation - Cloud Cover (strong negative)
    (6, 7): -0.71,  # UV Index - Cloud Cover (strong negative)
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
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Create heatmap with diverging colormap centered at zero
im = ax.imshow(masked_corr, cmap="BrBG", vmin=-1, vmax=1, aspect="equal")

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.ax.set_ylabel("Correlation Coefficient", fontsize=18, labelpad=15, color=INK)
cbar.ax.tick_params(labelsize=14, colors=INK_SOFT, labelcolor=INK_SOFT)

# Set ticks and labels with theme-adaptive coloring
ax.set_xticks(np.arange(n_vars))
ax.set_yticks(np.arange(n_vars))
ax.set_xticklabels(variables, fontsize=16, rotation=45, ha="right", rotation_mode="anchor", color=INK_SOFT)
ax.set_yticklabels(variables, fontsize=16, color=INK_SOFT)

# Add axis labels with theme-adaptive coloring
ax.set_xlabel("Weather Variables", fontsize=20, labelpad=15, color=INK)
ax.set_ylabel("Weather Variables", fontsize=20, labelpad=15, color=INK)

# Annotate cells with correlation values
for i in range(n_vars):
    for j in range(n_vars):
        if not mask[i, j]:  # Only annotate lower triangle and diagonal
            value = correlation_matrix[i, j]
            # Choose text color based on background brightness
            text_color = "white" if abs(value) > 0.5 else INK_SOFT
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", color=text_color, fontsize=14, fontweight="bold")

# Title with theme-adaptive coloring
ax.set_title("heatmap-correlation · matplotlib · pyplots.ai", fontsize=24, pad=20, fontweight="bold", color=INK)

# Remove spines
for spine in ax.spines.values():
    spine.set_visible(False)

# Adjust layout
plt.tight_layout()

# Save with theme-based filename and background
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
