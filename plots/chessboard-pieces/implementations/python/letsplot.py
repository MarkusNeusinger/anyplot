"""anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import os
import shutil

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    gggrid,
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

# Constants
FILES = "abcdefgh"
RANKS = "12345678"
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
LIGHT_SQUARE = "#F0D9B5"  # chess-standard board colors, identical in both themes
DARK_SQUARE = "#B58863"

# Columns: set these to your table's column names
SQUARE = "square"  # role: square
PIECE = "piece"  # role: piece

# Data: replace this block with your own position, one row per piece
# Scholar's Mate: a famous four-move checkmate
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
df = pd.DataFrame({SQUARE: list(pieces.keys()), PIECE: list(pieces.values())})

# Plot: board squares and piece positions derive from df and the constants
squares = pd.DataFrame(
    [
        {"file": i + 0.5, "rank": j + 0.5, "shade": "light" if (i + j) % 2 == 1 else "dark"}
        for i in range(len(FILES))
        for j in range(len(RANKS))
    ]
)
placed = pd.DataFrame(
    {
        "file": [FILES.index(sq[0]) + 0.5 for sq in df[SQUARE]],
        "rank": [RANKS.index(sq[1]) + 0.5 for sq in df[SQUARE]],
        "symbol": [PIECE_SYMBOLS[p] for p in df[PIECE]],
    }
)
ticks = [i + 0.5 for i in range(len(FILES))]

plot = (
    ggplot()
    + geom_tile(aes(x="file", y="rank", fill="shade"), data=squares, width=1, height=1, color="#8B7355", size=0.25)
    + scale_fill_manual(values={"light": LIGHT_SQUARE, "dark": DARK_SQUARE}, guide="none")
    + geom_text(aes(x="file", y="rank", label="symbol"), data=placed, size=14)
    + scale_x_continuous(breaks=ticks, labels=list(FILES), expand=[0, 0])
    + scale_y_continuous(breaks=ticks, labels=list(RANKS), expand=[0, 0])
    + coord_fixed(ratio=1)
    + labs(title="chessboard-pieces · python · letsplot · anyplot.ai")
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=12, hjust=0.5, face="bold", color=INK),
        axis_text=element_text(size=9, face="bold", color=INK_SOFT),
        axis_line=element_blank(),
        panel_border=element_blank(),
        plot_margin=20,
    )
)

# The fixed aspect leaves transparent strips: a one-panel grid paints the whole canvas
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save: ggsave writes into lets-plot-images, so move the files out
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")

if os.path.exists(f"lets-plot-images/plot-{THEME}.png"):
    shutil.move(f"lets-plot-images/plot-{THEME}.png", f"plot-{THEME}.png")
if os.path.exists(f"lets-plot-images/plot-{THEME}.html"):
    shutil.move(f"lets-plot-images/plot-{THEME}.html", f"plot-{THEME}.html")
if os.path.exists("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
