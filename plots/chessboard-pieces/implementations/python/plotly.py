"""anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: plotly 6.7.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-17
"""

import os

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (all eight positions); the board uses fixed traditional chess colors instead
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LIGHT_SQUARE = "#F0D9B5"
DARK_SQUARE = "#B58863"
WHITE_PIECE = "#FFFDF6"  # fill of white pieces
PIECE_INK = "#1A1A17"  # outline of white pieces and fill of black pieces
OUTLINE_GLYPHS = {"K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙"}
SOLID_GLYPHS = {"K": "♚", "Q": "♛", "R": "♜", "B": "♝", "N": "♞", "P": "♟"}
NAMES = {"K": "King", "Q": "Queen", "R": "Rook", "B": "Bishop", "N": "Knight", "P": "Pawn"}

# Columns: set these to your table's column names
SQUARE = "square"  # role: square
PIECE = "piece"  # role: piece

# Data: replace this block with your own table, for example df = pd.read_csv("position.csv")
# Position: Scholar's Mate, after 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6 4.Qxf7#
df = pd.DataFrame(
    {
        SQUARE: ["a8", "b8", "c8", "d8", "f8", "g8", "h8", "a7", "b7", "c7", "d7", "f7", "g7", "h7", "e6", "f3"]
        + ["e4", "c4", "a2", "b2", "c2", "d2", "f2", "g2", "h2", "a1", "b1", "c1", "d1", "e1", "h1"],
        PIECE: ["r", "n", "b", "q", "r", "n", "k", "p", "p", "p", "p", "Q", "p", "p", "p", "N"]
        + ["P", "B", "P", "P", "P", "P", "P", "P", "P", "R", "N", "B", "Q", "K", "R"],
    }
)

# Plot: reads only df and the constants above
df = df.assign(
    col=df[SQUARE].str[0].map(lambda f: ord(f) - ord("a")),
    row=df[SQUARE].str[1].astype(int) - 1,
    is_white=df[PIECE].str.isupper(),
    kind=df[PIECE].str.upper(),
)

fig = go.Figure()

# Board squares: a light square sits at h1 (col 7, row 0)
for row in range(8):
    for col in range(8):
        color = LIGHT_SQUARE if (row + col) % 2 == 1 else DARK_SQUARE
        fig.add_shape(
            type="rect", x0=col, y0=row, x1=col + 1, y1=row + 1, fillcolor=color, line={"width": 0}, layer="below"
        )

# Pieces: black = solid glyph in ink; white = solid cream glyph under an outline glyph in ink
for piece in df.itertuples():
    cx, cy = piece.col + 0.5, piece.row + 0.5
    if piece.is_white:
        fig.add_annotation(
            x=cx, y=cy, text=SOLID_GLYPHS[piece.kind], font={"size": 44, "color": WHITE_PIECE}, showarrow=False
        )
        glyph = OUTLINE_GLYPHS[piece.kind]
    else:
        glyph = SOLID_GLYPHS[piece.kind]
    fig.add_annotation(x=cx, y=cy, text=glyph, font={"size": 44, "color": PIECE_INK}, showarrow=False)

# Invisible hover targets: square and piece name on hover in the HTML version
fig.add_trace(
    go.Scatter(
        x=df["col"] + 0.5,
        y=df["row"] + 0.5,
        mode="markers",
        marker={"size": 30, "opacity": 0},
        text=[f"{'White' if w else 'Black'} {NAMES[k]}" for w, k in zip(df["is_white"], df["kind"], strict=True)],
        customdata=df[SQUARE],
        hovertemplate="%{text} on %{customdata}<extra></extra>",
        showlegend=False,
    )
)

# Coordinate labels outside the board rim: files a-h at the bottom, ranks 1-8 on the left
for i, file_letter in enumerate("abcdefgh"):
    fig.add_annotation(
        x=i + 0.5, y=-0.2, text=file_letter, font={"size": 16, "color": INK_SOFT}, showarrow=False, yanchor="top"
    )
    fig.add_annotation(
        x=-0.2, y=i + 0.5, text=str(i + 1), font={"size": 16, "color": INK_SOFT}, showarrow=False, xanchor="right"
    )

# Board border
fig.add_shape(type="rect", x0=0, y0=0, x1=8, y1=8, line={"color": INK_SOFT, "width": 1.5}, fillcolor="rgba(0,0,0,0)")

# Style
fig.update_layout(
    autosize=False,
    width=600,
    height=600,
    title={
        "text": "Scholar's Mate · chessboard-pieces · python · plotly · anyplot.ai",
        "font": {"size": 15, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"range": [-0.6, 8.2], "visible": False, "fixedrange": True, "scaleanchor": "y", "scaleratio": 1},
    yaxis={"range": [-0.6, 8.2], "visible": False, "fixedrange": True},
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 30, "r": 30, "t": 60, "b": 20},
    showlegend=False,
)

fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
