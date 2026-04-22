""" pyplots.ai
ternary-density: Ternary Density Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Polygon


# Data - Soil composition samples (sand/silt/clay percentages)
np.random.seed(42)

# Generate clustered compositional data
# Cluster 1: Sandy soils (high sand content)
n1 = 200
sand1 = np.random.beta(5, 2, n1) * 70 + 25
silt1 = np.random.beta(2, 3, n1) * (100 - sand1) * 0.6
clay1 = 100 - sand1 - silt1

# Cluster 2: Silty soils (high silt content)
n2 = 150
silt2 = np.random.beta(5, 2, n2) * 60 + 30
sand2 = np.random.beta(2, 3, n2) * (100 - silt2) * 0.5
clay2 = 100 - sand2 - silt2

# Cluster 3: Clay-rich soils
n3 = 150
clay3 = np.random.beta(4, 2, n3) * 50 + 30
sand3 = np.random.beta(2, 3, n3) * (100 - clay3) * 0.4
silt3 = 100 - clay3 - sand3

# Combine all samples
sand = np.concatenate([sand1, sand2, sand3])
silt = np.concatenate([silt1, silt2, silt3])
clay = np.concatenate([clay1, clay2, clay3])

# Transform ternary to Cartesian coordinates
# Convention: Sand at bottom-left, Silt at bottom-right, Clay at top
total = sand + silt + clay
sand_norm = sand / total
silt_norm = silt / total
clay_norm = clay / total
x = 0.5 * (2 * silt_norm + clay_norm)
y = (np.sqrt(3) / 2) * clay_norm

# Triangle vertices
sqrt3_2 = np.sqrt(3) / 2
vertices = np.array([[0, 0], [1, 0], [0.5, sqrt3_2]])

# Create figure (square format for symmetric ternary plot)
fig, ax = plt.subplots(figsize=(12, 12))

# Create clipping polygon for the triangle
triangle_clip = Polygon(vertices, transform=ax.transData)

# Draw subtle grid lines FIRST (10% intervals)
for i in range(1, 10):
    frac = i / 10
    # Lines parallel to bottom (constant clay proportion)
    x1, y1 = frac, 0
    x2, y2 = 0.5 + 0.5 * frac, sqrt3_2 * (1 - frac)
    ax.plot([x1, x2], [y1, y2], color="gray", alpha=0.25, linewidth=0.8, zorder=1)

    # Lines parallel to left side (constant silt proportion)
    x1, y1 = 0.5 * frac, sqrt3_2 * frac
    x2, y2 = 1 - 0.5 * frac, sqrt3_2 * frac
    ax.plot([x1, x2], [y1, y2], color="gray", alpha=0.25, linewidth=0.8, zorder=1)

    # Lines parallel to right side (constant sand proportion)
    x1, y1 = 0, 0
    x2, y2 = 0.5, sqrt3_2
    # Shift along the base
    x1, y1 = (1 - frac), 0
    x2, y2 = 0.5 + 0.5 * (1 - frac), sqrt3_2 * frac
    ax.plot([x1, x2], [y1, y2], color="gray", alpha=0.25, linewidth=0.8, zorder=1)

# Seaborn KDE plot for density visualization
sns.kdeplot(x=x, y=y, fill=True, cmap="viridis", levels=20, alpha=0.85, ax=ax, thresh=0.02, zorder=5)

# Apply clipping to the KDE contours
for collection in ax.collections:
    collection.set_clip_path(triangle_clip)

# Add contour lines for better interpretation
sns.kdeplot(x=x, y=y, levels=10, color="#306998", linewidths=1.2, ax=ax, zorder=6)

# Clip contour lines too
for collection in ax.collections:
    collection.set_clip_path(triangle_clip)

# Draw triangle boundary LAST (on top)
triangle_border = Polygon(vertices, fill=False, edgecolor="#306998", linewidth=4, zorder=15)
ax.add_patch(triangle_border)

# Vertex labels
ax.text(0, -0.08, "Sand (%)", ha="center", va="top", fontsize=22, fontweight="bold", color="#306998")
ax.text(1, -0.08, "Silt (%)", ha="center", va="top", fontsize=22, fontweight="bold", color="#306998")
ax.text(0.5, sqrt3_2 + 0.08, "Clay (%)", ha="center", va="bottom", fontsize=22, fontweight="bold", color="#306998")

# Percentage labels along edges
for i in [2, 4, 6, 8]:
    frac = i / 10
    # Bottom edge
    ax.text(frac, -0.04, f"{int(frac * 100)}", ha="center", va="top", fontsize=14, color="gray")
    # Left edge (clay axis)
    lx = 0.5 * frac
    ly = sqrt3_2 * frac
    ax.text(lx - 0.04, ly, f"{int(frac * 100)}", ha="right", va="center", fontsize=14, color="gray")
    # Right edge
    rx = 1 - 0.5 * frac
    ry = sqrt3_2 * frac
    ax.text(rx + 0.04, ry, f"{int(frac * 100)}", ha="left", va="center", fontsize=14, color="gray")

# Title
ax.set_title("Soil Composition · ternary-density · seaborn · pyplots.ai", fontsize=26, fontweight="bold", pad=25)

# Clean up axes
ax.set_xlim(-0.15, 1.15)
ax.set_ylim(-0.15, 1.05)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
