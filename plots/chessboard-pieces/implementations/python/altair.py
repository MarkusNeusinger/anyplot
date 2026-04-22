""" pyplots.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import altair as alt
import pandas as pd


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

# Famous position: Scholar's Mate (checkmate in 4 moves setup)
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
    "e7": "k",  # King exposed for Scholar's Mate setup
}

# Board square colors
LIGHT_SQUARE = "#F0D9B5"
DARK_SQUARE = "#B58863"

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
    alt.Chart(board_df)
    .mark_rect(stroke="#4a3728", strokeWidth=2)
    .encode(
        x=alt.X(
            "file:N",
            sort=file_order,
            axis=alt.Axis(
                title=None,
                labelFontSize=28,
                labelFontWeight="bold",
                labelColor="#4a3728",
                orient="bottom",
                ticks=False,
                domain=False,
                labelPadding=12,
            ),
        ),
        y=alt.Y(
            "rank:N",
            sort=rank_order,
            axis=alt.Axis(
                title=None,
                labelFontSize=28,
                labelFontWeight="bold",
                labelColor="#4a3728",
                orient="left",
                ticks=False,
                domain=False,
                labelPadding=12,
            ),
        ),
        color=alt.Color("color:N", scale=None, legend=None),
    )
)

# White pieces with dark outline for visibility on light squares
white_pieces = (
    alt.Chart(white_pieces_df)
    .mark_text(fontSize=70, fontWeight="bold", stroke="#2c2c2c", strokeWidth=1.5)
    .encode(
        x=alt.X("file:N", sort=file_order),
        y=alt.Y("rank:N", sort=rank_order),
        text="symbol:N",
        color=alt.value("#FAFAFA"),
    )
)

# Black pieces (solid black, clearly visible)
black_pieces = (
    alt.Chart(black_pieces_df)
    .mark_text(fontSize=70, fontWeight="bold")
    .encode(
        x=alt.X("file:N", sort=file_order),
        y=alt.Y("rank:N", sort=rank_order),
        text="symbol:N",
        color=alt.value("#1a1a1a"),
    )
)

# Combine layers
chart = (
    alt.layer(board, white_pieces, black_pieces)
    .properties(
        width=1000,
        height=1000,
        title=alt.Title(
            "Scholar's Mate Setup · chessboard-pieces · altair · pyplots.ai",
            fontSize=32,
            anchor="middle",
            color="#333333",
            offset=20,
        ),
    )
    .configure_view(strokeWidth=4, stroke="#4a3728")
)

# Save as PNG (square format: ~3600x3600 at scale 3.6)
chart.save("plot.png", scale_factor=3.6)

# Save as HTML for interactivity
chart.save("plot.html")
