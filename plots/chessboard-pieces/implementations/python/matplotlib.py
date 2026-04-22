""" pyplots.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-08
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt


# Unicode chess symbols
PIECE_SYMBOLS = {
    "K": "\u2654",  # White King
    "Q": "\u2655",  # White Queen
    "R": "\u2656",  # White Rook
    "B": "\u2657",  # White Bishop
    "N": "\u2658",  # White Knight
    "P": "\u2659",  # White Pawn
    "k": "\u265a",  # Black King
    "q": "\u265b",  # Black Queen
    "r": "\u265c",  # Black Rook
    "b": "\u265d",  # Black Bishop
    "n": "\u265e",  # Black Knight
    "p": "\u265f",  # Black Pawn
}

# Scholar's Mate position - a famous quick checkmate
# After 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6?? 4.Qxf7#
pieces = {
    # White pieces
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
    # Black pieces
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

# Create figure (square format for chessboard)
fig, ax = plt.subplots(figsize=(12, 12))

# Board colors (classic wooden board)
light_color = "#F0D9B5"  # Light squares
dark_color = "#B58863"  # Dark squares

# Draw board squares
for row in range(8):
    for col in range(8):
        # Light square at h1 (col=7, row=0), so (col + row) % 2 == 1 for light
        color = light_color if (col + row) % 2 == 1 else dark_color
        rect = patches.Rectangle((col, row), 1, 1, linewidth=0, facecolor=color)
        ax.add_patch(rect)

# Draw pieces
for square, piece in pieces.items():
    col = ord(square[0]) - ord("a")
    row = int(square[1]) - 1
    symbol = PIECE_SYMBOLS[piece]
    # Center piece in square
    ax.text(col + 0.5, row + 0.5, symbol, fontsize=56, ha="center", va="center", fontfamily="DejaVu Sans")

# Add coordinate labels
file_labels = "abcdefgh"
rank_labels = "12345678"

for i in range(8):
    # File labels (a-h) at bottom
    ax.text(i + 0.5, -0.35, file_labels[i], fontsize=20, ha="center", va="center", fontweight="bold", color="#306998")
    # Rank labels (1-8) on left
    ax.text(-0.35, i + 0.5, rank_labels[i], fontsize=20, ha="center", va="center", fontweight="bold", color="#306998")

# Board border
border = patches.Rectangle((0, 0), 8, 8, linewidth=4, edgecolor="#306998", facecolor="none")
ax.add_patch(border)

# Styling
ax.set_xlim(-0.6, 8.2)
ax.set_ylim(-0.6, 8.6)
ax.set_aspect("equal")
ax.axis("off")

# Title
ax.set_title(
    "Scholar's Mate · chessboard-pieces · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="bold",
    pad=20,
    color="#306998",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
