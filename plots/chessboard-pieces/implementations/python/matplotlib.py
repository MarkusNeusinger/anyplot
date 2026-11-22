"""anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
"""

import os

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Board colors (identical in both themes, as on a physical board)
LIGHT_SQUARE = "#F0D9B5"
DARK_SQUARE = "#B58863"
HIGHLIGHT = "#FFD700"  # mate-threat square

# Unicode chess symbols: white U+2654-2659, black U+265A-265F
PIECE_SYMBOLS = {
    "K": "♔",
    "Q": "♕",
    "R": "♖",
    "B": "♗",
    "N": "♘",
    "P": "♙",
    "k": "♚",
    "q": "♛",
    "r": "♜",
    "b": "♝",
    "n": "♞",
    "p": "♟",
}

# Column constants
SQUARE = "square"  # role: square
PIECE = "piece"  # role: piece

# Constants
MATE_SQUARE = "f7"  # square highlighted as the mate threat

# Data: Scholar's Mate after 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6?? 4.Qxf7#
position = {
    "a1": "R",
    "b1": "N",
    "c1": "B",
    "d1": "K",
    "h1": "R",
    "a2": "P",
    "b2": "P",
    "c2": "P",
    "d2": "P",
    "f2": "P",
    "g2": "P",
    "h2": "P",
    "c4": "B",
    "e4": "P",
    "f7": "Q",
    "a8": "r",
    "b8": "n",
    "c8": "b",
    "d8": "q",
    "e8": "k",
    "h8": "r",
    "a7": "p",
    "b7": "p",
    "c7": "p",
    "d7": "p",
    "g7": "p",
    "h7": "p",
    "c6": "n",
    "e5": "p",
    "f6": "n",
}
df = pd.DataFrame({SQUARE: list(position.keys()), PIECE: list(position.values())})

# Plot
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for row in range(8):
    for col in range(8):
        color = LIGHT_SQUARE if (col + row) % 2 == 1 else DARK_SQUARE
        ax.add_patch(patches.Rectangle((col, row), 1, 1, linewidth=0, facecolor=color))

# Highlight the mate square (the last piece's square: the queen delivering mate)
mate_col, mate_row = ord(MATE_SQUARE[0]) - ord("a"), int(MATE_SQUARE[1]) - 1
ax.add_patch(patches.Rectangle((mate_col, mate_row), 1, 1, linewidth=0, facecolor=HIGHLIGHT, alpha=0.15, zorder=2))

# Pieces centered on their squares
for square, piece in zip(df[SQUARE], df[PIECE], strict=True):
    col = ord(square[0]) - ord("a")
    row = int(square[1]) - 1
    ax.text(
        col + 0.5,
        row + 0.5,
        PIECE_SYMBOLS[piece],
        fontsize=34,
        ha="center",
        va="center",
        fontfamily="DejaVu Sans",
        zorder=3,
    )

# Coordinate labels at the rim: files a-h below, ranks 1-8 left
for i in range(8):
    ax.text(i + 0.5, -0.32, "abcdefgh"[i], fontsize=12, ha="center", va="center", fontweight="bold", color=INK)
    ax.text(-0.32, i + 0.5, "12345678"[i], fontsize=12, ha="center", va="center", fontweight="bold", color=INK)

ax.add_patch(patches.Rectangle((0, 0), 8, 8, linewidth=2, edgecolor=INK_SOFT, facecolor="none", zorder=4))

ax.set_xlim(-0.7, 8.3)
ax.set_ylim(-0.7, 8.7)
ax.set_aspect("equal")
ax.axis("off")

ax.set_title("chessboard-pieces · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", pad=8, color=INK)

fig.subplots_adjust(left=0.02, right=0.98, top=0.94, bottom=0.02)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
