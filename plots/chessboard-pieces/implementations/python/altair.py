""" anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: altair 6.3.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-22
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (not used for the board: chess squares keep their classic colors)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: the board and the piece set are fixed, whatever the position
FILES = list("abcdefgh")
RANKS = list("87654321")  # top to bottom, white at the bottom
LIGHT_SQUARE = "#F0D9B5"
DARK_SQUARE = "#B58863"
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

# A text font with the chess glyphs; the default fallback draws the black pawn as a color emoji
PIECE_FONT = "DejaVu Sans"

SQUARE = "Square"  # role: square
PIECE = "Piece"  # role: piece

# Data: replace this block with your own position, for example df = pd.DataFrame({SQUARE: [...], PIECE: [...]})
# Scholar's Mate setup: uppercase = white, lowercase = black
pieces = {
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
    "e7": "k",
}
df = pd.DataFrame({SQUARE: list(pieces), PIECE: list(pieces.values())})

# Plot
board = pd.DataFrame(
    [
        {"file": f, "rank": r, "color": LIGHT_SQUARE if (i + int(r)) % 2 == 1 else DARK_SQUARE}
        for i, f in enumerate(FILES)
        for r in RANKS
    ]
)
placed = pd.DataFrame(
    {
        "file": df[SQUARE].str[0],
        "rank": df[SQUARE].str[1],
        "symbol": df[PIECE].map(PIECE_SYMBOLS),
        "is_white": df[PIECE].str.isupper(),
    }
)

AXIS_STYLE = {"title": None, "labelFontSize": 15, "labelFontWeight": "bold", "labelColor": INK}
AXIS_STYLE |= {"ticks": False, "domain": False, "labelPadding": 6, "labelAngle": 0}
x_enc = alt.X("file", type="nominal", sort=FILES, axis=alt.Axis(orient="bottom", **AXIS_STYLE))
y_enc = alt.Y("rank", type="nominal", sort=RANKS, axis=alt.Axis(orient="left", **AXIS_STYLE))
x_pos = alt.X("file", type="nominal", sort=FILES)
y_pos = alt.Y("rank", type="nominal", sort=RANKS)

squares = (
    alt.Chart(board)
    .mark_rect(stroke=INK_SOFT, strokeWidth=0.5)
    .encode(x=x_enc, y=y_enc, color=alt.Color("color", type="nominal", scale=None, legend=None))
)

# White pieces: light fill with a dark outline so they read on light and dark squares
white_pieces = (
    alt.Chart(placed[placed["is_white"]])
    .mark_text(font=PIECE_FONT, fontSize=40, fontWeight="bold", stroke="#2C2C2C", strokeWidth=0.6, color="#FAFAFA")
    .encode(x=x_pos, y=y_pos, text=alt.Text("symbol", type="nominal"))
)

black_pieces = (
    alt.Chart(placed[~placed["is_white"]])
    .mark_text(font=PIECE_FONT, fontSize=40, fontWeight="bold", color="#1A1A1A")
    .encode(x=x_pos, y=y_pos, text=alt.Text("symbol", type="nominal"))
)

chart = (
    alt.layer(squares, white_pieces, black_pieces)
    .properties(
        width=440,
        height=440,
        background=PAGE_BG,
        title=alt.Title(
            "Scholar's Mate Setup · chessboard-pieces · python · altair · anyplot.ai",
            fontSize=14,
            anchor="middle",
            color=INK,
            offset=10,
        ),
    )
    .configure_view(strokeWidth=1.5, stroke=INK_SOFT, fill=PAGE_BG)
)

# Save: render, then pad (never crop) to the 2400 x 2400 square canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TARGET = 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET or img.height > TARGET:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET}x{TARGET}; shrink width/height")
canvas = Image.new("RGB", (TARGET, TARGET), PAGE_BG)
canvas.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
