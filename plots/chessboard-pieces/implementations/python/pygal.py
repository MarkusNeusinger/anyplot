""" anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: pygal 3.1.0 | Python 3.13.13
Quality: 80/100 | Created: 2026-05-17
"""

import importlib
import os
import sys
import xml.etree.ElementTree as ET


# This file is named pygal.py; strip its directory from sys.path so that
# importlib resolves to the installed package, not this script itself.
_self_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.realpath(p or ".") != _self_dir]

pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style

ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
LIGHT_SQUARE = "#E8D5C4" if THEME == "light" else "#4A4136"
DARK_SQUARE = "#B5956F" if THEME == "light" else "#2D2622"
WHITE_PIECE_COLOR = "#F5E6D0"
BLACK_PIECE_COLOR = "#1A1A17"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

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
    "e2": "P",
    "f2": "P",
    "g2": "P",
    "h2": "P",
    "a7": "p",
    "b7": "p",
    "c7": "p",
    "d7": "p",
    "e7": "p",
    "f7": "p",
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
}

# Pygal Style — maps ANYPLOT_THEME tokens to pygal's chrome
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=72,
    label_font_size=40,
    major_label_font_size=40,
    legend_font_size=36,
)

# pygal.XY renders the SVG skeleton: title, background, and theme chrome
chart = pygal.XY(
    width=3600,
    height=3600,
    title="chessboard-pieces · pygal · anyplot.ai",
    style=custom_style,
    show_legend=False,
    show_x_guides=False,
    show_y_guides=False,
    show_dots=False,
    show_x_labels=False,
    show_y_labels=False,
    margin=80,
)
chart.add("", [(0, 0)])  # single invisible seed point — show_dots=False hides it

# Render via pygal to get the themed SVG base
svg_bytes = chart.render()

# Inject chess board elements into pygal's SVG tree
root = ET.fromstring(svg_bytes)
NS = "http://www.w3.org/2000/svg"

BOARD_SIZE = 2800
MARGIN_X = (3600 - BOARD_SIZE) // 2  # 400 px side margins
MARGIN_Y = 210  # clears title + top margin
SQ = BOARD_SIZE // 8  # 350 px per square

board_g = ET.SubElement(root, f"{{{NS}}}g", attrib={"id": "chess-board"})

# 64 alternating squares — h1 (file=7, rank=0): (7+0)%2==1 → light ✓
for rank in range(8):
    for file in range(8):
        x = MARGIN_X + file * SQ
        y = MARGIN_Y + (7 - rank) * SQ
        fill = LIGHT_SQUARE if (file + rank) % 2 == 1 else DARK_SQUARE
        ET.SubElement(
            board_g,
            f"{{{NS}}}rect",
            attrib={"x": str(x), "y": str(y), "width": str(SQ), "height": str(SQ), "fill": fill},
        )

# Pieces — white pieces cream, black pieces near-black for visual distinction
for sq_name, piece in pieces.items():
    file = ord(sq_name[0]) - ord("a")
    rank = int(sq_name[1]) - 1
    cx = MARGIN_X + file * SQ + SQ // 2
    cy = MARGIN_Y + (7 - rank) * SQ + SQ // 2
    t = ET.SubElement(
        board_g,
        f"{{{NS}}}text",
        attrib={
            "x": str(cx),
            "y": str(cy),
            "font-size": str(int(SQ * 0.7)),
            "text-anchor": "middle",
            "dominant-baseline": "central",
            "fill": WHITE_PIECE_COLOR if piece.isupper() else BLACK_PIECE_COLOR,
        },
    )
    t.text = PIECE_UNICODE[piece]

# File labels (a–h)
for file in range(8):
    t = ET.SubElement(
        board_g,
        f"{{{NS}}}text",
        attrib={
            "x": str(MARGIN_X + file * SQ + SQ // 2),
            "y": str(MARGIN_Y + BOARD_SIZE + 55),
            "font-size": "44",
            "text-anchor": "middle",
            "fill": INK_MUTED,
        },
    )
    t.text = chr(ord("a") + file)

# Rank labels (1–8)
for rank in range(8):
    t = ET.SubElement(
        board_g,
        f"{{{NS}}}text",
        attrib={
            "x": str(MARGIN_X - 30),
            "y": str(MARGIN_Y + (7 - rank) * SQ + SQ // 2),
            "font-size": "44",
            "text-anchor": "end",
            "dominant-baseline": "central",
            "fill": INK_MUTED,
        },
    )
    t.text = str(rank + 1)

# Serialize — register_namespace calls above keep default SVG namespace prefix clean
svg_content = ET.tostring(root, encoding="unicode")

with open(f"plot-{THEME}.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

try:
    import cairosvg

    cairosvg.svg2png(bytestring=svg_content.encode(), write_to=f"plot-{THEME}.png")
except ImportError:
    pass

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        f'<!DOCTYPE html><html><head><meta charset="utf-8">'
        f"<style>body{{margin:0;background:{PAGE_BG}}}</style></head>"
        f"<body>{svg_content}</body></html>"
    )
