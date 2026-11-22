"""anyplot.ai
chessboard-basic: Chess Board Grid Visualization
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (not used for the board: a chess board is a classic two-tone scheme)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Chess board colors (theme-adaptive)
LIGHT_SQUARE = "#F0D9B5" if THEME == "light" else "#E8D4C4"
DARK_SQUARE = "#B58863" if THEME == "light" else "#6B5047"
BORDER_COLOR = "#5D4037" if THEME == "light" else "#A0967C"

# Columns: set these to your table's column names
COLUMN = "Column"  # role: columns
ROW = "Row"  # role: rows

# Data: replace this block with your own table, one row per square
df = pd.DataFrame({COLUMN: list("abcdefgh") * 8, ROW: [str(rank) for rank in range(1, 9) for _ in range(8)]})

# Plot: reads only df and the constants above
files = list(dict.fromkeys(df[COLUMN]))
ranks = list(dict.fromkeys(df[ROW]))

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for col, row in zip(df[COLUMN].map(files.index), df[ROW].map(ranks.index), strict=True):
    # h1 (last column, first row) is light, so an odd column + row index sum is light
    color = LIGHT_SQUARE if (row + col) % 2 == 1 else DARK_SQUARE
    ax.add_patch(Rectangle((col, row), 1, 1, facecolor=color, edgecolor=BORDER_COLOR, linewidth=0.6))

ax.set_xlim(0, len(files))
ax.set_ylim(0, len(ranks))
ax.set_aspect("equal")

# Column labels at the bottom, row labels on the left, each centered on its square
ax.set_xticks([i + 0.5 for i in range(len(files))], files)
ax.set_yticks([i + 0.5 for i in range(len(ranks))], ranks)
ax.tick_params(axis="both", length=0, pad=6, labelsize=13, labelcolor=INK)
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontweight("bold")

for spine in ax.spines.values():
    spine.set_linewidth(1.6)
    spine.set_color(BORDER_COLOR)

ax.set_title("chessboard-basic · python · matplotlib · anyplot.ai", fontsize=13, fontweight="bold", color=INK, pad=12)

fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
