""" anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os
import sys


# Handle import conflict when script is named altair.py
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != script_dir and p not in ("", ".")]

import altair as chart_module  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Chess board squares (standard colors, theme-independent)
LIGHT_SQUARE = "#F0D9B5"
DARK_SQUARE = "#B58863"
BOARD_BORDER = INK_SOFT

# Unicode chess pieces mapping
PIECE_SYMBOLS = {
    "K": "♔",
    "Q": "♕",
    "R": "♖",
    "B": "♗",
    "N": "♘",
    "P": "♙",  # White
    "k": "♚",
    "q": "♛",
    "r": "♜",
    "b": "♝",
    "n": "♞",
    "p": "♟",  # Black
}

# Scholar's Mate position: Famous tactical pattern
pieces = {
    # White pieces
    "a1": "R",
    "b1": "N",
    "c1": "B",
    "d1": "Q",
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
    "c4": "B",
    "h5": "Q",
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
    "f7": "p",
    "g7": "p",
    "h7": "p",
    "e5": "p",
    "f6": "n",
    "e7": "k",  # King exposed for checkmate threat
}

# Create board squares data
files = "abcdefgh"
board_data = []
for col_idx, file in enumerate(files):
    for row in range(1, 9):
        square = f"{file}{row}"
        is_light = (col_idx + row) % 2 == 1
        color = LIGHT_SQUARE if is_light else DARK_SQUARE
        board_data.append({"file": file, "rank": str(row), "color": color, "square": square})

board_df = pd.DataFrame(board_data)

# Create pieces data - separate white and black for styling
white_pieces_data = []
black_pieces_data = []

for square, piece in pieces.items():
    file = square[0]
    rank = square[1]
    symbol = PIECE_SYMBOLS[piece]
    is_white = piece.isupper()
    piece_data = {"file": file, "rank": rank, "symbol": symbol, "piece": piece}
    if is_white:
        white_pieces_data.append(piece_data)
    else:
        black_pieces_data.append(piece_data)

white_pieces_df = pd.DataFrame(white_pieces_data)
black_pieces_df = pd.DataFrame(black_pieces_data)

# Define ordering for file and rank
file_order = list("abcdefgh")
rank_order = list("87654321")  # Top to bottom in standard chess view

# Create board squares layer
board = (
    chart_module.Chart(board_df)
    .mark_rect(stroke=BOARD_BORDER, strokeWidth=2)
    .encode(
        x=chart_module.X(
            "file:N",
            sort=file_order,
            axis=chart_module.Axis(
                title=None,
                labelFontSize=28,
                labelFontWeight="bold",
                labelColor=INK,
                orient="bottom",
                ticks=False,
                domain=False,
                labelPadding=12,
            ),
        ),
        y=chart_module.Y(
            "rank:N",
            sort=rank_order,
            axis=chart_module.Axis(
                title=None,
                labelFontSize=28,
                labelFontWeight="bold",
                labelColor=INK,
                orient="left",
                ticks=False,
                domain=False,
                labelPadding=12,
            ),
        ),
        color=chart_module.Color("color:N", scale=None, legend=None),
    )
)

# White pieces with dark outline for visibility
white_pieces = (
    chart_module.Chart(white_pieces_df)
    .mark_text(fontSize=70, fontWeight="bold", stroke="#2c2c2c", strokeWidth=1.5)
    .encode(
        x=chart_module.X("file:N", sort=file_order),
        y=chart_module.Y("rank:N", sort=rank_order),
        text="symbol:N",
        color=chart_module.value("#FAFAFA"),
    )
)

# Black pieces (solid black, clearly visible)
black_pieces = (
    chart_module.Chart(black_pieces_df)
    .mark_text(fontSize=70, fontWeight="bold")
    .encode(
        x=chart_module.X("file:N", sort=file_order),
        y=chart_module.Y("rank:N", sort=rank_order),
        text="symbol:N",
        color=chart_module.value("#1a1a1a"),
    )
)

# Combine layers
chart = (
    chart_module.layer(board, white_pieces, black_pieces)
    .properties(
        width=1000,
        height=1000,
        background=PAGE_BG,
        title=chart_module.Title(
            "Scholar's Mate Setup · chessboard-pieces · altair · anyplot.ai",
            fontSize=32,
            anchor="middle",
            color=INK,
            offset=20,
        ),
    )
    .configure_view(strokeWidth=4, stroke=BOARD_BORDER, fill=PAGE_BG)
)

# Save as PNG and HTML (square format: 3600x3600 at scale 3.6)
png_path = os.path.join(script_dir, f"plot-{THEME}.png")
html_path = os.path.join(script_dir, f"plot-{THEME}.html")
chart.save(png_path, scale_factor=3.6)
chart.save(html_path)
