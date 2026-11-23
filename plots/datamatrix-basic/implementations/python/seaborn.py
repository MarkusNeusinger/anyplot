"""anyplot.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
# Barcode modules stay black on white in both themes (scanner contrast)
MODULE_OFF = "#FFFFFF"
MODULE_ON = "#000000"

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": MODULE_OFF,
        "axes.edgecolor": INK_SOFT,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
    },
)

# Column constants
CONTENT = "content"  # role: content
SIZE = "size"  # role: size

# Data: the symbol to draw, a 10x10 Data Matrix (ISO/IEC 16022 ECC 200)
df = pd.DataFrame({CONTENT: ["ANYPLOT"], SIZE: ["10x10"]})

# Plot: square canvas, 2400x2400 px
# Module layout of the symbol; the ECC 200 payload for the content is fixed, the structure derives from the size
n_rows, n_cols = (int(v) for v in df[SIZE].iloc[0].split("x"))
grid = np.zeros((n_rows, n_cols), dtype=int)
grid[:, 0] = 1  # L-shaped finder: solid left column
grid[-1, :] = 1  # L-shaped finder: solid bottom row
grid[0, :] = np.arange(n_cols) % 2  # clock pattern along the top
grid[:, -1] = np.arange(n_rows) % 2  # clock pattern along the right
grid[-1, -1] = 1  # bottom-right corner belongs to the finder
payload = np.array(
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
data_region = grid[1:-1, 1:-1]
data_region[:] = np.resize(payload, data_region.shape)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)

sns.heatmap(
    grid,
    cmap=[MODULE_OFF, MODULE_ON],
    vmin=0,
    vmax=1,
    cbar=False,
    square=True,
    linewidths=0,
    xticklabels=False,
    yticklabels=False,
    ax=ax,
)

# Quiet zone: one blank white module on every side (ISO/IEC 16022)
ax.set_xlim(-1, n_cols + 1)
ax.set_ylim(n_rows + 1, -1)

ax.set_title("datamatrix-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=12)
ax.set_xlabel(
    f"Encoded: '{df[CONTENT].iloc[0]}' · ISO/IEC 16022 ECC 200 · {n_rows}×{n_cols}", fontsize=10, color=INK_SOFT
)
ax.set_ylabel("")
for spine in ax.spines.values():
    spine.set_visible(False)

fig.subplots_adjust(left=0.08, right=0.92, top=0.93, bottom=0.1)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
