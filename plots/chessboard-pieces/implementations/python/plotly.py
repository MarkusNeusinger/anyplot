""" pyplots.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: plotly 6.5.1 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-08
"""

import plotly.graph_objects as go


# Chess piece Unicode symbols
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

# Example position: Scholar's Mate (checkmate in 4 moves)
pieces = {
    "a8": "r",
    "b8": "n",
    "c8": "b",
    "d8": "q",
    "f8": "r",
    "g8": "n",
    "h8": "k",
    "a7": "p",
    "b7": "p",
    "c7": "p",
    "d7": "p",
    "f7": "Q",
    "g7": "p",
    "h7": "p",
    "e6": "p",
    "f3": "N",
    "e4": "P",
    "c4": "B",
    "a2": "P",
    "b2": "P",
    "c2": "P",
    "d2": "P",
    "f2": "P",
    "g2": "P",
    "h2": "P",
    "a1": "R",
    "b1": "N",
    "c1": "B",
    "d1": "Q",
    "e1": "K",
    "h1": "R",
}

# Board colors
LIGHT_SQUARE = "#F0D9B5"
DARK_SQUARE = "#B58863"

# Create figure
fig = go.Figure()

# Draw board squares
for row in range(8):
    for col in range(8):
        is_light = (row + col) % 2 == 1
        color = LIGHT_SQUARE if is_light else DARK_SQUARE
        fig.add_shape(type="rect", x0=col, y0=row, x1=col + 1, y1=row + 1, fillcolor=color, line={"width": 0})

# Add pieces as text annotations
for square, piece in pieces.items():
    col = ord(square[0]) - ord("a")
    row = int(square[1]) - 1
    symbol = PIECE_SYMBOLS.get(piece, "")

    fig.add_annotation(
        x=col + 0.5,
        y=row + 0.5,
        text=symbol,
        font={"size": 70, "color": "#000000", "family": "Arial"},
        showarrow=False,
        xanchor="center",
        yanchor="middle",
    )

# Add file labels (a-h) at bottom
for col, file_letter in enumerate("abcdefgh"):
    fig.add_annotation(
        x=col + 0.5,
        y=-0.25,
        text=file_letter,
        font={"size": 32, "color": "#333333"},
        showarrow=False,
        xanchor="center",
        yanchor="top",
    )

# Add rank labels (1-8) on left
for row in range(8):
    fig.add_annotation(
        x=-0.25,
        y=row + 0.5,
        text=str(row + 1),
        font={"size": 32, "color": "#333333"},
        showarrow=False,
        xanchor="right",
        yanchor="middle",
    )

# Layout
fig.update_layout(
    title={
        "text": "Scholar's Mate · chessboard-pieces · plotly · pyplots.ai",
        "font": {"size": 36, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "range": [-0.6, 8],
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "fixedrange": True,
        "scaleanchor": "y",
        "scaleratio": 1,
    },
    yaxis={"range": [-0.6, 8], "showgrid": False, "zeroline": False, "showticklabels": False, "fixedrange": True},
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 60, "r": 60, "t": 100, "b": 60},
    showlegend=False,
)

# Add board border
fig.add_shape(type="rect", x0=0, y0=0, x1=8, y1=8, line={"color": "#333333", "width": 3}, fillcolor="rgba(0,0,0,0)")

# Save as PNG (square format for chess board)
fig.write_image("plot.png", width=1200, height=1200, scale=3)

# Save interactive HTML
fig.write_html("plot.html")
