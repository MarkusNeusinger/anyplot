""" pyplots.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import os
import shutil

import pandas as pd
from lets_plot import (  # noqa: F401
    LetsPlot,
    aes,
    coord_fixed,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)


LetsPlot.setup_html()

# Unicode chess symbols
PIECE_SYMBOLS = {
    "K": "\u2654",
    "Q": "\u2655",
    "R": "\u2656",
    "B": "\u2657",
    "N": "\u2658",
    "P": "\u2659",
    "k": "\u265a",
    "q": "\u265b",
    "r": "\u265c",
    "b": "\u265d",
    "n": "\u265e",
    "p": "\u265f",
}

# Scholar's Mate position - a famous 4-move checkmate
pieces = {
    "a1": "R",
    "b1": "N",
    "c1": "B",
    "d1": "Q",
    "e1": "K",
    "f1": "B",
    "g1": "N",
    "h1": "R",
    "a2": "P",
    "b2": "P",
    "c2": "P",
    "d2": "P",
    "f2": "P",
    "g2": "P",
    "h2": "P",
    "e4": "P",
    "c4": "B",
    "f7": "Q",
    "a7": "p",
    "b7": "p",
    "c7": "p",
    "d7": "p",
    "g7": "p",
    "h7": "p",
    "a8": "r",
    "b8": "n",
    "c8": "b",
    "d8": "q",
    "e8": "k",
    "f8": "b",
    "g8": "n",
    "h8": "r",
    "e5": "p",
    "f6": "n",
}

# Create board squares data
files = "abcdefgh"
squares_data = []
for i in range(8):
    for j in range(8):
        is_light = (i + j) % 2 == 1
        squares_data.append({"file": i + 0.5, "rank": j + 0.5, "color": "light" if is_light else "dark"})
df_squares = pd.DataFrame(squares_data)

# Create pieces data
pieces_data = []
for square, piece in pieces.items():
    file_idx = files.index(square[0]) + 0.5
    rank_val = int(square[1]) - 0.5
    symbol = PIECE_SYMBOLS.get(piece, "")
    pieces_data.append({"file": file_idx, "rank": rank_val, "symbol": symbol})
df_pieces = pd.DataFrame(pieces_data)

# Board colors
light_color = "#F0D9B5"
dark_color = "#B58863"

# Build the plot
plot = (
    ggplot()
    + geom_tile(aes(x="file", y="rank", fill="color"), data=df_squares, width=1, height=1, color="#8B7355", size=0.5)
    + scale_fill_manual(values={"light": light_color, "dark": dark_color}, guide="none")
    + geom_text(aes(x="file", y="rank", label="symbol"), data=df_pieces, size=28)
    + scale_x_continuous(
        breaks=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5], labels=["a", "b", "c", "d", "e", "f", "g", "h"]
    )
    + scale_y_continuous(
        breaks=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5], labels=["1", "2", "3", "4", "5", "6", "7", "8"]
    )
    + coord_fixed(ratio=1)
    + labs(title="Scholar's Mate · chessboard-pieces · letsplot · pyplots.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=24, hjust=0.5, face="bold"),
        axis_text=element_text(size=18, face="bold"),
        plot_margin=40,
    )
    + ggsize(1200, 1200)
)

# Save outputs - ggsave uses lets-plot-images subfolder by default
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")

# Move files from lets-plot-images to current directory
if os.path.exists("lets-plot-images/plot.png"):
    shutil.move("lets-plot-images/plot.png", "plot.png")
if os.path.exists("lets-plot-images/plot.html"):
    shutil.move("lets-plot-images/plot.html", "plot.html")
if os.path.exists("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
