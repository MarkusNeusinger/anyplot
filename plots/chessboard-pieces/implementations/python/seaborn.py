""" pyplots.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-08
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Chess piece Unicode symbols
PIECE_SYMBOLS = {
    "K": "\u2654",
    "Q": "\u2655",
    "R": "\u2656",
    "B": "\u2657",
    "N": "\u2658",
    "P": "\u2659",  # White pieces
    "k": "\u265a",
    "q": "\u265b",
    "r": "\u265c",
    "b": "\u265d",
    "n": "\u265e",
    "p": "\u265f",  # Black pieces
}

# Example position: Scholar's Mate (4-move checkmate)
# Position after 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6?? 4.Qxf7#
pieces = {
    # White pieces
    "a1": "R",
    "b1": "N",
    "c1": "B",
    "e1": "K",
    "f1": "B",
    "h1": "R",
    "a2": "P",
    "b2": "P",
    "c2": "P",
    "d2": "P",
    "f2": "P",
    "g2": "P",
    "h2": "P",
    "e4": "P",
    "f7": "Q",  # Checkmate position!
    # Black pieces
    "a8": "r",
    "b8": "n",
    "c8": "b",
    "d8": "q",
    "f8": "b",
    "h8": "r",
    "a7": "p",
    "b7": "p",
    "c7": "p",
    "d7": "p",
    "g7": "p",
    "h7": "p",
    "e8": "k",  # King in checkmate
    "e5": "p",
    "c6": "n",
    "f6": "n",
}

# Create board data for heatmap
# h1 should be light (chess standard), so pattern needs adjustment
board_colors = np.zeros((8, 8))
for row in range(8):
    for col in range(8):
        # Checkerboard pattern: h1 (row=7, col=7) should be light (0)
        board_colors[row, col] = (row + col + 1) % 2

# Create figure with square aspect ratio for chessboard
fig, ax = plt.subplots(figsize=(12, 12))

# Use seaborn heatmap for the board squares
sns.heatmap(
    board_colors,
    ax=ax,
    cmap=["#F0D9B5", "#B58863"],  # Classic chess board colors
    cbar=False,
    square=True,
    linewidths=0.5,
    linecolor="#8B7355",
    xticklabels=list("abcdefgh"),
    yticklabels=list("87654321"),
)

# Style tick labels
ax.tick_params(
    axis="both",
    which="both",
    length=0,
    labelsize=20,
    labelbottom=True,
    labeltop=False,
    labelleft=True,
    labelright=False,
)
ax.set_xticklabels(list("abcdefgh"), fontsize=20, fontweight="bold")
ax.set_yticklabels(list("87654321"), fontsize=20, fontweight="bold")

# Place pieces on the board
for square, piece in pieces.items():
    col = ord(square[0]) - ord("a")  # a=0, b=1, ..., h=7
    row = 8 - int(square[1])  # 8=0, 7=1, ..., 1=7

    symbol = PIECE_SYMBOLS.get(piece, "")
    # White pieces in white, black pieces in black
    color = "#1a1a1a" if piece.islower() else "#ffffff"
    # Add slight shadow/outline for visibility on both light and dark squares
    ax.text(
        col + 0.5,
        row + 0.5,
        symbol,
        fontsize=48,
        ha="center",
        va="center",
        color=color,
        fontweight="bold",
        path_effects=[pe.withStroke(linewidth=2, foreground="#666666")],
    )

# Title
ax.set_title("Scholar's Mate · chessboard-pieces · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Remove axis labels
ax.set_xlabel("")
ax.set_ylabel("")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
