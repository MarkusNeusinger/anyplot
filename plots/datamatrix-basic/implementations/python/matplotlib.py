""" anyplot.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-20
"""

import importlib
import os
import sys


# This file is named matplotlib.py, which shadows the installed matplotlib package.
# Remove the script directory from sys.path so Python finds the real package.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _here]
del _here

plt = importlib.import_module("matplotlib.pyplot")
np = importlib.import_module("numpy")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data - 20x20 Data Matrix for electronics component traceability
np.random.seed(42)
size = 20
content = "PCB:2026-A3F7"

# Initialize matrix (0 = white, 1 = black)
matrix = np.zeros((size, size), dtype=int)

# L-shaped finder pattern: solid black left column and bottom row
matrix[:, 0] = 1
matrix[-1, :] = 1

# Alternating timing pattern on top row and right column
for i in range(size):
    matrix[0, i] = i % 2  # top row: alternating, starts white
    matrix[i, -1] = (i + 1) % 2  # right col: alternating, starts black

# Interior data: deterministic pattern seeded from content bytes
content_seed = sum(ord(c) for c in content)
interior = np.random.RandomState(content_seed).randint(0, 2, size=(size - 2, size - 2))
matrix[1:-1, 1:-1] = interior

# Plot (square canvas: 2400×2400 px)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor("white")  # barcode spec requires white cell background for scan contrast

# Render Data Matrix using pcolormesh for crisp cell boundaries
x_coords = np.arange(size + 1)
y_coords = np.arange(size + 1)
ax.pcolormesh(x_coords, y_coords, matrix[::-1], cmap="binary", edgecolors="none", linewidth=0)

ax.set_aspect("equal")
quiet_zone = 1.5
ax.set_xlim(-quiet_zone, size + quiet_zone)
ax.set_ylim(-quiet_zone, size + quiet_zone)
ax.axis("off")

# Title
ax.set_title("datamatrix-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=12)

# Annotations below barcode
fig.text(
    0.5,
    0.055,
    f"Data Matrix 20×20  ·  Encoded: {content}",
    ha="center",
    va="bottom",
    fontsize=9,
    fontfamily="monospace",
    color=INK_SOFT,
)
fig.text(
    0.5,
    0.02,
    "L-finder (left+bottom)  ·  Timing (top+right)  ·  ECC 200",
    ha="center",
    va="bottom",
    fontsize=8,
    color=INK_MUTED,
)

plt.tight_layout(rect=[0, 0.09, 1, 1])
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
