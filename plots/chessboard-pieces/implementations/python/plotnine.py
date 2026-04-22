""" pyplots.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-08
"""

import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Unicode chess symbols mapping
UNICODE_PIECES = {
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

# Scholar's Mate position - a famous 4-move checkmate
pieces = {
    # White pieces
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
    "f3": "N",
    "c4": "B",
    "f7": "Q",  # White Queen delivers checkmate
    # Black pieces
    "a8": "r",
    "b8": "n",
    "c8": "b",
    "d8": "q",
    "f8": "b",
    "g8": "n",
    "h8": "r",
    "a7": "p",
    "b7": "p",
    "c7": "p",
    "d7": "p",
    "g7": "p",
    "h7": "p",
    "e5": "p",
    "e8": "k",  # Black King in checkmate
}

# Create board data
files = list("abcdefgh")
ranks = list(range(1, 9))

board_data = []
for file_idx, file in enumerate(files):
    for rank in ranks:
        square = f"{file}{rank}"
        is_light = (file_idx + rank) % 2 == 1
        color = "light" if is_light else "dark"
        board_data.append({"file": file_idx + 1, "rank": rank, "color": color, "square": square})

board_df = pd.DataFrame(board_data)

# Create pieces data
pieces_data = []
for square, piece in pieces.items():
    file = files.index(square[0]) + 1
    rank = int(square[1])
    unicode_piece = UNICODE_PIECES.get(piece, "")
    pieces_data.append({"file": file, "rank": rank, "piece": unicode_piece})

pieces_df = pd.DataFrame(pieces_data)

# Color scheme for board squares
board_colors = {"light": "#F0D9B5", "dark": "#B58863"}

# Create the plot
plot = (
    ggplot()
    + geom_tile(data=board_df, mapping=aes(x="file", y="rank", fill="color"), width=1, height=1)
    + scale_fill_manual(values=board_colors)
    + geom_text(
        data=pieces_df, mapping=aes(x="file", y="rank", label="piece"), size=28, family="DejaVu Sans", color="#000000"
    )
    + scale_x_continuous(breaks=list(range(1, 9)), labels=list("abcdefgh"), expand=(0, 0))
    + scale_y_continuous(breaks=list(range(1, 9)), labels=[str(i) for i in range(1, 9)], expand=(0, 0))
    + coord_fixed(ratio=1)
    + labs(title="Scholar's Mate · chessboard-pieces · plotnine · pyplots.ai")
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        axis_title=element_blank(),
        axis_text_x=element_text(size=20, weight="bold"),
        axis_text_y=element_text(size=20, weight="bold"),
        axis_ticks=element_blank(),
        panel_background=element_rect(fill="#FFFFFF"),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="#FFFFFF"),
        legend_position="none",
    )
)

plot.save("plot.png", dpi=300, width=12, height=12)
