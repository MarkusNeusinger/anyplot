""" anyplot.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": "white",
        "axes.edgecolor": INK_SOFT,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
    },
)

# Data — 10x10 Data Matrix (ISO/IEC 16022 ECC 200) encoding "ANYPLOT"
np.random.seed(42)
size = 10
matrix = np.zeros((size, size), dtype=int)

# L-shaped finder pattern: solid black left column and bottom row
matrix[:, 0] = 1
matrix[-1, :] = 1

# Alternating clock pattern: top row and right column
for i in range(size):
    matrix[0, i] = i % 2
for i in range(size):
    matrix[i, -1] = i % 2

# Interior 8x8 data region (simulated ECC 200 payload for "ANYPLOT")
data_pattern = np.array(
    [
        [1, 0, 1, 1, 0, 1, 0, 1],
        [0, 1, 1, 0, 1, 0, 1, 0],
        [1, 0, 0, 1, 1, 1, 0, 1],
        [0, 1, 1, 0, 0, 1, 1, 0],
        [1, 1, 0, 1, 0, 0, 1, 0],
        [0, 0, 1, 0, 1, 1, 0, 1],
        [1, 0, 1, 1, 0, 0, 1, 0],
        [0, 1, 0, 0, 1, 1, 0, 1],
    ]
)
matrix[1 : size - 1, 1 : size - 1] = data_pattern

# Plot — square canvas (2400x2400 px: figsize=(6,6) dpi=400)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)

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

# Quiet zone: 1-module white border around the barcode (ISO/IEC 16022 requirement)
ax.set_xlim(-1, size + 1)
ax.set_ylim(size + 1, -1)

# Style
ax.set_title("datamatrix-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=12)
for spine in ax.spines.values():
    spine.set_visible(False)

ax.set_facecolor("white")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
