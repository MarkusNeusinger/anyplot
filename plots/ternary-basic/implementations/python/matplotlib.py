""" pyplots.ai
ternary-basic: Basic Ternary Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Soil composition samples (sand, silt, clay summing to 100%)
np.random.seed(42)
n_points = 50

# Generate random compositions that sum to 100 using Dirichlet distribution
raw = np.random.dirichlet([2, 2, 2], n_points) * 100
sand = raw[:, 0]  # Component A (top vertex)
silt = raw[:, 1]  # Component B (bottom-left vertex)
clay = raw[:, 2]  # Component C (bottom-right vertex)

# Convert ternary coordinates to Cartesian (equilateral triangle)
# Triangle: A at top (0.5, sqrt(3)/2), B at bottom-left (0, 0), C at bottom-right (1, 0)
# Formula: x = 0.5 * (2*c + a) / (a+b+c), y = sqrt(3)/2 * a / (a+b+c)
sqrt3_2 = np.sqrt(3) / 2
total = sand + silt + clay
x_points = 0.5 * (2 * clay + sand) / total
y_points = sqrt3_2 * sand / total

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Draw triangle outline
triangle_x = [0.5, 0, 1, 0.5]
triangle_y = [sqrt3_2, 0, 0, sqrt3_2]
ax.plot(triangle_x, triangle_y, color="black", linewidth=2.5)

# Draw grid lines at 20% intervals
grid_levels = [0.2, 0.4, 0.6, 0.8]
for level in grid_levels:
    # Lines parallel to bottom edge (constant A/sand)
    a_val = level
    x1 = 0.5 * (2 * (1 - a_val) + a_val)
    y1 = sqrt3_2 * a_val
    x2 = 0.5 * (2 * 0 + a_val)
    y2 = sqrt3_2 * a_val
    ax.plot([x1, x2], [y1, y2], color="gray", alpha=0.3, linewidth=1.5, linestyle="--")

    # Lines parallel to right edge (constant B/silt)
    b_val = level
    x1 = 0.5 * (2 * (1 - b_val) + 0)
    y1 = sqrt3_2 * 0
    x2 = 0.5 * (2 * 0 + (1 - b_val))
    y2 = sqrt3_2 * (1 - b_val)
    ax.plot([x1, x2], [y1, y2], color="gray", alpha=0.3, linewidth=1.5, linestyle="--")

    # Lines parallel to left edge (constant C/clay)
    c_val = level
    x1 = 0.5 * (2 * c_val + 0)
    y1 = sqrt3_2 * 0
    x2 = 0.5 * (2 * c_val + (1 - c_val))
    y2 = sqrt3_2 * (1 - c_val)
    ax.plot([x1, x2], [y1, y2], color="gray", alpha=0.3, linewidth=1.5, linestyle="--")

# Add tick labels at 20% intervals along each edge
tick_fontsize = 14
for level in [0, 20, 40, 60, 80, 100]:
    frac = level / 100

    # Sand axis (A) - along left edge from bottom to top
    x_tick = 0.5 * (2 * 0 + frac)
    y_tick = sqrt3_2 * frac
    ax.text(x_tick - 0.06, y_tick, f"{level}", fontsize=tick_fontsize, ha="right", va="center")

    # Silt axis (B) - along bottom edge from right to left
    x_tick = 0.5 * (2 * (1 - frac) + 0)
    y_tick = 0
    ax.text(x_tick, y_tick - 0.05, f"{level}", fontsize=tick_fontsize, ha="center", va="top")

    # Clay axis (C) - along right edge from top to bottom
    x_tick = 0.5 * (2 * frac + (1 - frac))
    y_tick = sqrt3_2 * (1 - frac)
    ax.text(x_tick + 0.06, y_tick, f"{level}", fontsize=tick_fontsize, ha="left", va="center")

# Plot data points
ax.scatter(x_points, y_points, s=200, color="#306998", alpha=0.7, edgecolors="white", linewidth=1.5, zorder=5)

# Add vertex labels with component names
label_fontsize = 20
ax.text(0.5, sqrt3_2 + 0.1, "Sand (%)", fontsize=label_fontsize, ha="center", va="bottom", fontweight="bold")
ax.text(-0.08, -0.08, "Silt (%)", fontsize=label_fontsize, ha="right", va="top", fontweight="bold")
ax.text(1.08, -0.08, "Clay (%)", fontsize=label_fontsize, ha="left", va="top", fontweight="bold")

# Title
ax.set_title("Soil Composition · ternary-basic · matplotlib · pyplots.ai", fontsize=24, pad=20)

# Clean up axes
ax.set_aspect("equal")
ax.axis("off")

# Adjust limits to prevent clipping
ax.set_xlim(-0.25, 1.25)
ax.set_ylim(-0.2, 1.1)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
