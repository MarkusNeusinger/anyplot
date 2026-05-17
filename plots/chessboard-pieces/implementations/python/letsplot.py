"""anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-05-17
"""

import os
import shutil

import pandas as pd
from lets_plot import (  # noqa: F401
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
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

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Unicode chess symbols
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

# Board colors (chess standard, theme-independent for clarity)
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
    + labs(title="chessboard-pieces · letsplot · anyplot.ai")
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=24, hjust=0.5, face="bold", color=INK),
        axis_text=element_text(size=18, face="bold", color=INK_SOFT),
        axis_line=element_blank(),
        plot_margin=40,
    )
    + ggsize(1200, 1200)
)

# Save outputs - ggsave uses lets-plot-images subfolder by default
ggsave(plot, f"plot-{THEME}.png", scale=3)
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images to current directory
if os.path.exists(f"lets-plot-images/plot-{THEME}.png"):
    shutil.move(f"lets-plot-images/plot-{THEME}.png", f"plot-{THEME}.png")
if os.path.exists(f"lets-plot-images/plot-{THEME}.html"):
    shutil.move(f"lets-plot-images/plot-{THEME}.html", f"plot-{THEME}.html")
if os.path.exists("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
