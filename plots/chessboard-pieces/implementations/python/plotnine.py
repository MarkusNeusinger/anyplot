"""anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Constants
FILES = "abcdefgh"
# Filled glyphs for both sides: white pieces are drawn as white fill over a dark outline
GLYPHS = {"k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"}
BOARD_LIGHT = "#F0D9B5"  # chess tradition, identical in both themes
BOARD_DARK = "#B58863"
PIECE_WHITE = "#FFFFFF"
PIECE_BLACK = "#000000"

# Columns: set these to your table's column names
SQUARE = "square"  # role: square
PIECE = "piece"  # role: piece

# Data: replace this block with your own position, for example df = pd.read_csv("position.csv")
# Lucena position (rook endgame, White to move): K+R+P against K+R
df = pd.DataFrame({SQUARE: ["d8", "d7", "f1", "g7", "g2"], PIECE: ["K", "P", "R", "k", "r"]})

# Plot
# Board: 64 squares, a light square at h1 (file index + rank is even)
board = pd.DataFrame(
    [
        {"file": i + 1, "rank": rank, "tone": "light" if (i + rank) % 2 == 0 else "dark"}
        for i in range(len(FILES))
        for rank in range(1, len(FILES) + 1)
    ]
)

# Pieces: grid position from the square name, filled glyph from the lowercase code
pos = df.assign(
    file=df[SQUARE].str[0].map(FILES.index) + 1,
    rank=df[SQUARE].str[1].astype(int),
    glyph=df[PIECE].str.lower().map(GLYPHS),
    is_white=df[PIECE].str.isupper(),
)
white = pos[pos["is_white"]]
black = pos[~pos["is_white"]]

plot = (
    ggplot()
    + geom_tile(data=board, mapping=aes(x="file", y="rank", fill="tone"), width=1, height=1)
    + scale_fill_manual(values={"light": BOARD_LIGHT, "dark": BOARD_DARK})
    # Dark outline under the white pieces, then the white fill on top
    + geom_text(
        data=white, mapping=aes(x="file", y="rank", label="glyph"), size=41, family="DejaVu Sans", color=PIECE_BLACK
    )
    + geom_text(
        data=white, mapping=aes(x="file", y="rank", label="glyph"), size=38, family="DejaVu Sans", color=PIECE_WHITE
    )
    + geom_text(
        data=black, mapping=aes(x="file", y="rank", label="glyph"), size=38, family="DejaVu Sans", color=PIECE_BLACK
    )
    + scale_x_continuous(breaks=range(1, len(FILES) + 1), labels=list(FILES), expand=(0, 0))
    + scale_y_continuous(
        breaks=range(1, len(FILES) + 1), labels=[str(r) for r in range(1, len(FILES) + 1)], expand=(0, 0)
    )
    + coord_fixed(ratio=1)
    + labs(title="Lucena Position · chessboard-pieces · python · plotnine · anyplot.ai")
    + theme(
        figure_size=(6, 6),
        plot_title=element_text(size=11, ha="center", weight="bold", color=INK),
        axis_title=element_blank(),
        axis_text_x=element_text(size=12, weight="bold", color=INK_SOFT),
        axis_text_y=element_text(size=12, weight="bold", color=INK_SOFT),
        axis_ticks=element_blank(),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG),
        legend_position="none",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
