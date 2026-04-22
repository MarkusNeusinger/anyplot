""" pyplots.ai
ternary-density: Ternary Density Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-11
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde


np.random.seed(42)

# Generate compositional data (sand/silt/clay sediment analysis)
# Create 3 clusters representing different sediment types

# Cluster 1: Sandy sediments (high sand)
n1 = 300
sand1 = np.random.beta(5, 2, n1) * 60 + 35
silt1 = np.random.beta(2, 3, n1) * (100 - sand1) * 0.6
clay1 = 100 - sand1 - silt1

# Cluster 2: Silty sediments (high silt)
n2 = 250
silt2 = np.random.beta(5, 2, n2) * 50 + 40
sand2 = np.random.beta(2, 4, n2) * (100 - silt2) * 0.5
clay2 = 100 - sand2 - silt2

# Cluster 3: Clay-rich sediments (high clay)
n3 = 250
clay3 = np.random.beta(4, 2, n3) * 45 + 40
sand3 = np.random.beta(2, 5, n3) * (100 - clay3) * 0.4
silt3 = 100 - sand3 - clay3

# Combine all clusters
sand = np.concatenate([sand1, sand2, sand3])
silt = np.concatenate([silt1, silt2, silt3])
clay = np.concatenate([clay1, clay2, clay3])

# Ensure non-negative values and normalize to sum to 100
sand = np.clip(sand, 0, 100)
silt = np.clip(silt, 0, 100)
clay = np.clip(clay, 0, 100)
total = sand + silt + clay
sand = sand / total * 100
silt = silt / total * 100
clay = clay / total * 100


# Convert ternary to Cartesian coordinates
def ternary_to_cartesian(a, b, c):
    """Convert ternary (a, b, c) to Cartesian (x, y)."""
    total = a + b + c
    a, b, c = a / total, b / total, c / total
    x = 0.5 * (2 * b + c)
    y = (np.sqrt(3) / 2) * c
    return x, y


# Convert data points
x_data, y_data = ternary_to_cartesian(sand, silt, clay)

# Create density grid
grid_resolution = 200
xi = np.linspace(0, 1, grid_resolution)
yi = np.linspace(0, np.sqrt(3) / 2, grid_resolution)
Xi, Yi = np.meshgrid(xi, yi)

# Convert grid to ternary to check if inside triangle
# For point (x, y): c = y * 2/sqrt(3), b = x - c/2, a = 1 - b - c
Ci = Yi * 2 / np.sqrt(3)
Bi = Xi - Ci / 2
Ai = 1 - Bi - Ci

# Mask points outside the triangle
mask = (Ai >= 0) & (Bi >= 0) & (Ci >= 0) & (Ai <= 1) & (Bi <= 1) & (Ci <= 1)

# Compute KDE
data_points = np.vstack([x_data, y_data])
kde = gaussian_kde(data_points, bw_method="silverman")

# Evaluate KDE on grid
positions = np.vstack([Xi.ravel(), Yi.ravel()])
Z = kde(positions).reshape(Xi.shape)
Z = np.where(mask, Z, np.nan)

# Create figure
fig, ax = plt.subplots(figsize=(12, 12))

# Draw triangle boundary
triangle = plt.Polygon(
    [[0, 0], [1, 0], [0.5, np.sqrt(3) / 2]], fill=False, edgecolor="#333333", linewidth=2.5, zorder=10
)
ax.add_patch(triangle)

# Draw grid lines inside triangle
grid_levels = [0.2, 0.4, 0.6, 0.8]
for level in grid_levels:
    # Lines parallel to each edge
    # Parallel to bottom (constant c)
    c_val = level
    x_start, y_start = ternary_to_cartesian(1 - c_val, 0, c_val)
    x_end, y_end = ternary_to_cartesian(0, 1 - c_val, c_val)
    ax.plot([x_start, x_end], [y_start, y_end], color="#888888", linewidth=1, alpha=0.4, linestyle="--", zorder=1)

    # Parallel to left edge (constant b)
    b_val = level
    x_start, y_start = ternary_to_cartesian(1 - b_val, b_val, 0)
    x_end, y_end = ternary_to_cartesian(0, b_val, 1 - b_val)
    ax.plot([x_start, x_end], [y_start, y_end], color="#888888", linewidth=1, alpha=0.4, linestyle="--", zorder=1)

    # Parallel to right edge (constant a)
    a_val = level
    x_start, y_start = ternary_to_cartesian(a_val, 0, 1 - a_val)
    x_end, y_end = ternary_to_cartesian(a_val, 1 - a_val, 0)
    ax.plot([x_start, x_end], [y_start, y_end], color="#888888", linewidth=1, alpha=0.4, linestyle="--", zorder=1)

# Plot density heatmap
density_plot = ax.contourf(Xi, Yi, Z, levels=20, cmap="viridis", alpha=0.85, zorder=2)

# Add contour lines
ax.contour(Xi, Yi, Z, levels=6, colors="white", linewidths=1.5, alpha=0.6, zorder=3)

# Add colorbar
cbar = plt.colorbar(density_plot, ax=ax, shrink=0.7, pad=0.02)
cbar.set_label("Density", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Add vertex labels
ax.text(0, -0.05, "Sand (%)", fontsize=20, ha="center", va="top", fontweight="bold")
ax.text(1, -0.05, "Silt (%)", fontsize=20, ha="center", va="top", fontweight="bold")
ax.text(0.5, np.sqrt(3) / 2 + 0.05, "Clay (%)", fontsize=20, ha="center", va="bottom", fontweight="bold")

# Add percentage labels along edges
for pct in [20, 40, 60, 80]:
    # Bottom edge (Sand-Silt)
    ax.text(pct / 100, -0.03, f"{pct}", fontsize=14, ha="center", va="top", color="#555555")
    # Left edge (Sand-Clay)
    x, y = ternary_to_cartesian(100 - pct, 0, pct)
    ax.text(x - 0.04, y, f"{pct}", fontsize=14, ha="right", va="center", color="#555555")
    # Right edge (Silt-Clay)
    x, y = ternary_to_cartesian(0, 100 - pct, pct)
    ax.text(x + 0.04, y, f"{pct}", fontsize=14, ha="left", va="center", color="#555555")

# Title
ax.set_title("Sediment Composition Analysis\nternary-density · matplotlib · pyplots.ai", fontsize=24, pad=20)

# Set axis properties
ax.set_xlim(-0.1, 1.1)
ax.set_ylim(-0.15, np.sqrt(3) / 2 + 0.15)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
