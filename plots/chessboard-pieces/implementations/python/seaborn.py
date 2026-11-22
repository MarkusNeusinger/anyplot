"""anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-17
"""

import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (the board and pieces use chess-specific tones instead)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
FILES = "abcdefgh"
RANKS = "12345678"
# Solid glyphs (U+265A to U+265F) for both sides: color, not outline shape, tells the sides apart
SYMBOLS = {"k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"}
BOARD_LIGHT = "#EEEED2"  # tournament-style cream
BOARD_DARK = "#769656"  # tournament-style green
WHITE_FILL = "#FFFDF6"
BLACK_FILL = "#1A1A17"

# Columns: set these to your table's column names
SQUARE = "Square"  # role: square
PIECE = "Piece"  # role: piece

# Data: replace this block with your own position, uppercase = white, lowercase = black
# Position: Fried Liver Attack after 1.e4 e5 2.Nf3 Nc6 3.Bc4 Nf6 4.Ng5 d5 5.exd5 Nxd5
position = {
    "a1": "R",
    "b1": "N",
    "c1": "B",
    "d1": "Q",
    "e1": "K",
    "h1": "R",
    "a2": "P",
    "b2": "P",
    "c2": "P",
    "d2": "P",
    "f2": "P",
    "g2": "P",
    "h2": "P",
    "c4": "B",
    "f3": "N",
    "g5": "N",
    "a8": "r",
    "b8": "n",
    "c8": "b",
    "d8": "q",
    "e8": "k",
    "f8": "b",
    "h8": "r",
    "a7": "p",
    "b7": "p",
    "c7": "p",
    "e7": "p",
    "f7": "p",
    "g7": "p",
    "h7": "p",
    "d5": "n",
    "f6": "n",
    "c6": "n",
}
df = pd.DataFrame({SQUARE: list(position.keys()), PIECE: list(position.values())})

# Plot
# Board shade per cell: row 0 is rank 8; the h1 corner (row 7, col 7) is a light square (0)
rows, cols = np.indices((8, 8))
board = (rows + cols + 1) % 2

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)

sns.heatmap(
    board,
    ax=ax,
    cmap=[BOARD_LIGHT, BOARD_DARK],
    cbar=False,
    square=True,
    linewidths=0,
    xticklabels=list(FILES),
    yticklabels=list(reversed(RANKS)),
)

ax.tick_params(axis="both", which="both", length=0, labelsize=14, pad=6)
ax.set_xticklabels(list(FILES), fontsize=14, fontweight="bold", color=INK_SOFT)
ax.set_yticklabels(list(reversed(RANKS)), fontsize=14, fontweight="bold", color=INK_SOFT, rotation=0)

# Pieces: centered in their squares, sized with a margin to the edges
for square, piece in zip(df[SQUARE], df[PIECE], strict=True):
    col = FILES.index(square[0])
    row = 8 - int(square[1])
    is_white = piece.isupper()
    ax.text(
        col + 0.5,
        row + 0.55,
        SYMBOLS[piece.lower()],
        fontsize=30,
        ha="center",
        va="center",
        color=WHITE_FILL if is_white else BLACK_FILL,
        path_effects=[pe.withStroke(linewidth=1.4, foreground=BLACK_FILL if is_white else WHITE_FILL)],
    )

ax.set_xlabel("")
ax.set_ylabel("")
ax.set_title(
    "Italian Game · chessboard-pieces · python · seaborn · anyplot.ai",
    fontsize=10,
    fontweight="bold",
    pad=14,
    color=INK,
)

fig.tight_layout()
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
