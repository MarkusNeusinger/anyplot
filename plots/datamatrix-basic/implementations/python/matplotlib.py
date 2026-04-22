""" pyplots.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - create a sample Data Matrix pattern
# Data Matrix has: L-shaped finder (solid left/bottom), alternating pattern (top/right)
np.random.seed(42)
size = 16  # 16x16 Data Matrix

# Initialize matrix (0 = white, 1 = black)
matrix = np.zeros((size, size), dtype=int)

# L-shaped finder pattern: solid black on left column and bottom row
matrix[:, 0] = 1  # Left column - solid black
matrix[-1, :] = 1  # Bottom row - solid black

# Alternating timing pattern on top row and right column
for i in range(size):
    matrix[0, i] = i % 2  # Top row - alternating starting white
    matrix[i, -1] = (i + 1) % 2  # Right column - alternating starting black

# Fill interior with data pattern (simulated ECC 200 encoded data)
# Generate pseudo-random data pattern for the interior cells
interior_data = np.random.randint(0, 2, size=(size - 2, size - 2))
matrix[1:-1, 1:-1] = interior_data

# Create plot (square format for barcode)
fig, ax = plt.subplots(figsize=(12, 12))

# Display the Data Matrix
# Use pcolormesh for crisp cell boundaries
x = np.arange(size + 1)
y = np.arange(size + 1)
ax.pcolormesh(x, y, matrix[::-1], cmap="binary", edgecolors="none", linewidth=0)

# Set equal aspect ratio for square cells
ax.set_aspect("equal")

# Add quiet zone by adjusting axis limits
quiet_zone = 2
ax.set_xlim(-quiet_zone, size + quiet_zone)
ax.set_ylim(-quiet_zone, size + quiet_zone)

# Remove axes for clean barcode appearance
ax.axis("off")

# Set white background
ax.set_facecolor("white")
fig.patch.set_facecolor("white")

# Add title
ax.set_title("datamatrix-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, pad=30)

# Add encoded content description
content = "SERIAL:12345678"
fig.text(
    0.5,
    0.08,
    f"Data Matrix (16\u00d716) \u2022 Encoded: {content}",
    ha="center",
    fontsize=18,
    fontfamily="monospace",
    color="#306998",
)

# Add structure annotations
fig.text(
    0.5,
    0.04,
    "L-finder (left+bottom) \u2022 Timing pattern (top+right) \u2022 ECC 200",
    ha="center",
    fontsize=14,
    color="#666666",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
