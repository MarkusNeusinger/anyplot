""" pyplots.ai
ternary-basic: Basic Ternary Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seaborn style
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.2)

# Data - Soil composition samples (Sand, Silt, Clay)
np.random.seed(42)
n_points = 50

# Generate random compositions that sum to 100
raw = np.random.dirichlet(alpha=[2, 2, 2], size=n_points) * 100
df = pd.DataFrame({"Sand": raw[:, 0], "Silt": raw[:, 1], "Clay": raw[:, 2]})

# Ternary coordinates transformation (vectorized)
# Convert (a, b, c) to Cartesian (x, y) where a + b + c = 100
# Triangle vertices: Bottom-left (0,0)=Sand, Bottom-right (1,0)=Silt, Top (0.5, sqrt(3)/2)=Clay
sqrt3_2 = np.sqrt(3) / 2
sand_norm = df["Sand"].values / 100
silt_norm = df["Silt"].values / 100
clay_norm = df["Clay"].values / 100
x = 0.5 * (2 * silt_norm + clay_norm)
y = sqrt3_2 * clay_norm

# Create plot
fig, ax = plt.subplots(figsize=(12, 12))

# Draw triangle outline
triangle = np.array([[0, 0], [1, 0], [0.5, sqrt3_2], [0, 0]])
ax.plot(triangle[:, 0], triangle[:, 1], "k-", linewidth=2, zorder=5)

# Draw grid lines at 10% intervals
grid_color = "#888888"
grid_alpha = 0.3
grid_lw = 1

for level in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    # Lines parallel to bottom (constant Clay)
    x1, y1 = 0.5 * level, sqrt3_2 * level
    x2, y2 = 1 - 0.5 * level, sqrt3_2 * level
    ax.plot([x1, x2], [y1, y2], color=grid_color, alpha=grid_alpha, linewidth=grid_lw, zorder=1)

    # Lines parallel to left edge (constant Silt)
    x1, y1 = level, 0
    x2, y2 = 0.5 + 0.5 * level, sqrt3_2 * (1 - level)
    ax.plot([x1, x2], [y1, y2], color=grid_color, alpha=grid_alpha, linewidth=grid_lw, zorder=1)

    # Lines parallel to right edge (constant Sand)
    x1, y1 = 0.5 * (1 - level), sqrt3_2 * (1 - level)
    x2, y2 = 1 - level, 0
    ax.plot([x1, x2], [y1, y2], color=grid_color, alpha=grid_alpha, linewidth=grid_lw, zorder=1)

# Add tick marks along edges (at 20% intervals)
tick_length = 0.02

for level in [0.2, 0.4, 0.6, 0.8]:
    # Bottom edge ticks (Silt percentage increasing left to right)
    ax.plot([level, level], [-tick_length, 0], "k-", linewidth=1.5, zorder=5)
    ax.text(level, -0.05, f"{int(level * 100)}%", ha="center", va="top", fontsize=14)

    # Left edge ticks (Clay percentage)
    x_tick = 0.5 * level
    y_tick = sqrt3_2 * level
    dx, dy = -tick_length * np.cos(np.pi / 6), -tick_length * np.sin(np.pi / 6)
    ax.plot([x_tick, x_tick + dx], [y_tick, y_tick + dy], "k-", linewidth=1.5, zorder=5)
    ax.text(x_tick + dx - 0.03, y_tick + dy + 0.01, f"{int(level * 100)}%", ha="right", va="center", fontsize=14)

    # Right edge ticks (Clay percentage from right side)
    x_tick = 1 - 0.5 * level
    y_tick = sqrt3_2 * level
    dx, dy = tick_length * np.cos(np.pi / 6), -tick_length * np.sin(np.pi / 6)
    ax.plot([x_tick, x_tick + dx], [y_tick, y_tick + dy], "k-", linewidth=1.5, zorder=5)
    ax.text(x_tick + dx + 0.03, y_tick + dy + 0.01, f"{int(level * 100)}%", ha="left", va="center", fontsize=14)

# Plot data points using seaborn
scatter_df = pd.DataFrame({"x": x, "y": y})
sns.scatterplot(
    data=scatter_df, x="x", y="y", ax=ax, color="#306998", s=200, alpha=0.7, edgecolor="white", linewidth=1.5, zorder=10
)

# Vertex labels
label_offset = 0.08
ax.text(0, -label_offset, "Sand (100%)", ha="center", va="top", fontsize=20, fontweight="bold")
ax.text(1, -label_offset, "Silt (100%)", ha="center", va="top", fontsize=20, fontweight="bold")
ax.text(0.5, sqrt3_2 + label_offset, "Clay (100%)", ha="center", va="bottom", fontsize=20, fontweight="bold")

# Title
ax.set_title("Soil Composition · ternary-basic · seaborn · pyplots.ai", fontsize=24, pad=20)

# Clean up axes
ax.set_xlim(-0.15, 1.15)
ax.set_ylim(-0.18, 1.05)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
