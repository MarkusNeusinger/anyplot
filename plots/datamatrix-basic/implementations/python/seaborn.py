""" pyplots.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Create a Data Matrix pattern
# Data Matrix uses L-shaped finder pattern (solid black on left and bottom)
# and alternating timing pattern on top and right edges

np.random.seed(42)

# Matrix size (10x10 is a standard small Data Matrix size)
size = 10

# Create the matrix with encoded data pattern (simulated)
matrix = np.zeros((size, size), dtype=int)

# L-shaped finder pattern: solid black on left column and bottom row
matrix[:, 0] = 1  # Left column - solid black
matrix[-1, :] = 1  # Bottom row - solid black

# Alternating timing pattern on top row and right column
# Top row: alternating starting with white (0)
for i in range(size):
    matrix[0, i] = i % 2
# Right column: alternating starting with white (0)
for i in range(size):
    matrix[i, -1] = i % 2

# Fill interior with data pattern (simulated encoded data for "PYPLOTS")
# This represents the encoded data region
data_pattern = [
    [1, 0, 1, 1, 0, 1, 0, 1],
    [0, 1, 0, 1, 1, 0, 1, 0],
    [1, 1, 0, 0, 1, 0, 1, 1],
    [0, 0, 1, 1, 0, 1, 0, 0],
    [1, 0, 1, 0, 0, 1, 1, 0],
    [0, 1, 1, 0, 1, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 1, 0],
    [0, 1, 0, 1, 0, 1, 1, 1],
]

# Place data pattern in interior (rows 1-8, columns 1-8)
for i in range(8):
    for j in range(8):
        matrix[i + 1, j + 1] = data_pattern[i][j]

# Create figure with quiet zone (white border around the code)
fig, ax = plt.subplots(figsize=(12, 12))

# Plot heatmap - invert matrix so 1=black, 0=white
sns.heatmap(
    matrix,
    cmap=["white", "black"],
    cbar=False,
    square=True,
    linewidths=0,
    linecolor="white",
    xticklabels=False,
    yticklabels=False,
    ax=ax,
)

# Add quiet zone by setting axis limits with padding
ax.set_xlim(-1, size + 1)
ax.set_ylim(size + 1, -1)  # Invert y-axis for proper orientation

# Title
ax.set_title("datamatrix-basic · seaborn · pyplots.ai", fontsize=24, pad=20)

# Remove spines for cleaner look
for spine in ax.spines.values():
    spine.set_visible(False)

# Set background to white (quiet zone)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
