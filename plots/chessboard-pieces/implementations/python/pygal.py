""" anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: pygal 3.1.3 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-22
"""

import importlib
import os
import sys

import cairosvg
import pandas as pd


# This file is named pygal.py; strip its directory from sys.path so that
# importlib resolves to the installed package, not this script itself.
_self_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.realpath(p or ".") != _self_dir]

pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
LIGHT_SQUARE = "#E8D5C4" if THEME == "light" else "#4A4136"
DARK_SQUARE = "#B5956F" if THEME == "light" else "#2D2622"
WHITE_PIECE_COLOR = "#F5E6D0"
BLACK_PIECE_COLOR = "#1A1A17"
# Thin outlines keep both piece colors readable on light and dark squares in either theme
WHITE_PIECE_EDGE = "#1A1A17"
BLACK_PIECE_EDGE = "#F5E6D0" if THEME == "dark" else "#1A1A17"

IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

PIECE_UNICODE = {
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

# Columns: set these to your table's column names
SQUARE = "Square"  # role: square
PIECE = "Piece"  # role: piece

# Data: replace this block with your own position, for example df = pd.read_csv("position.csv")
_back_rank = "RNBQKBNR"
_squares = [f"{f}{r}" for r in "12" for f in "abcdefgh"] + [f"{f}{r}" for r in "78" for f in "abcdefgh"]
_codes = list(_back_rank) + ["P"] * 8 + ["p"] * 8 + list(_back_rank.lower())
df = pd.DataFrame({SQUARE: _squares, PIECE: _codes})

# Plot
# Pygal Style — maps ANYPLOT_THEME tokens to pygal's chrome
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=52,
    label_font_size=40,
    major_label_font_size=40,
    legend_font_size=36,
)

# pygal.XY renders the SVG skeleton: title, background, and theme chrome
chart = pygal.XY(
    width=2400,
    height=2400,
    title="chessboard-pieces · python · pygal · anyplot.ai",
    style=custom_style,
    show_legend=False,
    show_x_guides=False,
    show_y_guides=False,
    show_dots=False,
    show_x_labels=False,
    show_y_labels=False,
    margin=60,
)
chart.add("", [(0, 0)])  # single invisible seed point — show_dots=False hides it

# Render via pygal to get the themed SVG base
svg_bytes = chart.render()

# Inject chess board elements into pygal's SVG document
CANVAS = 2400
BOARD_SIZE = 1840
MARGIN_X = (CANVAS - BOARD_SIZE) // 2
MARGIN_Y = 220  # clears title + top margin
SQ = BOARD_SIZE // 8
FILES = "abcdefgh"
RANKS = "12345678"

parts = ['<g id="chess-board">']

# 64 alternating squares — h1 (file=7, rank=0): (7+0)%2==1 → light ✓
for rank in range(len(RANKS)):
    for file in range(len(FILES)):
        x = MARGIN_X + file * SQ
        y = MARGIN_Y + (len(RANKS) - 1 - rank) * SQ
        fill = LIGHT_SQUARE if (file + rank) % 2 == 1 else DARK_SQUARE
        parts.append(f'<rect x="{x}" y="{y}" width="{SQ}" height="{SQ}" fill="{fill}"/>')

# Pieces: a solid glyph carries the body color, the hollow glyph on top draws the outline
for sq_name, piece in zip(df[SQUARE], df[PIECE], strict=True):
    file = FILES.index(sq_name[0])
    rank = RANKS.index(sq_name[1])
    cx = MARGIN_X + file * SQ + SQ // 2
    cy = MARGIN_Y + (len(RANKS) - 1 - rank) * SQ + SQ // 2
    is_white = piece.isupper()
    layers = (
        (PIECE_UNICODE[piece.lower()], WHITE_PIECE_COLOR if is_white else BLACK_PIECE_COLOR),
        (PIECE_UNICODE[piece.upper()], WHITE_PIECE_EDGE if is_white else BLACK_PIECE_EDGE),
    )
    for glyph, color in layers:
        parts.append(
            f'<text x="{cx}" y="{cy}" font-size="{int(SQ * 0.7)}" text-anchor="middle" '
            f'dominant-baseline="central" fill="{color}">{glyph}</text>'
        )

# File labels (a–h) below the board, rank labels (1–8) left of it
for file, letter in enumerate(FILES):
    parts.append(
        f'<text x="{MARGIN_X + file * SQ + SQ // 2}" y="{MARGIN_Y + BOARD_SIZE + 50}" font-size="40" '
        f'text-anchor="middle" fill="{INK_MUTED}">{letter}</text>'
    )
for rank, number in enumerate(RANKS):
    parts.append(
        f'<text x="{MARGIN_X - 24}" y="{MARGIN_Y + (len(RANKS) - 1 - rank) * SQ + SQ // 2}" font-size="40" '
        f'text-anchor="end" dominant-baseline="central" fill="{INK_MUTED}">{number}</text>'
    )
parts.append("</g>")

svg_text = svg_bytes.decode("utf-8")
svg_content = svg_text[: svg_text.rindex("</svg>")] + "".join(parts) + "</svg>"
html_content = (
    f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>body{{margin:0;background:{PAGE_BG}}}</style></head>'
    f"<body>{svg_content}</body></html>"
)

# Save
cairosvg.svg2png(bytestring=svg_content.encode(), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
