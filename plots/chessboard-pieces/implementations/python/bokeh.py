""" anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-17
"""

import os
import time
from pathlib import Path

from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Unicode chess piece symbols
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

# Scholar's Mate position - a famous quick checkmate
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
    "f3": "N",
    "f7": "Q",  # Moved pieces including checkmate queen
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
    "g7": "p",
    "h7": "p",
    "e5": "p",
    "e8": "k",  # King in check
}

# Create figure with square aspect ratio for chess board
p = figure(
    width=3600,
    height=3600,
    title="Scholar's Mate · chessboard-pieces · bokeh · anyplot.ai",
    x_range=(-0.5, 7.5),
    y_range=(-0.5, 7.5),
    tools="pan,wheel_zoom,reset",
    toolbar_location="right",
)

# Draw the chess board squares
light_squares_x = []
light_squares_y = []
dark_squares_x = []
dark_squares_y = []

for row in range(8):
    for col in range(8):
        is_light = (row + col) % 2 == 1  # h1 (7, 0) should be light
        if is_light:
            light_squares_x.append(col)
            light_squares_y.append(row)
        else:
            dark_squares_x.append(col)
            dark_squares_y.append(row)

# Draw squares using rect glyphs
light_source = ColumnDataSource(data={"x": light_squares_x, "y": light_squares_y})
dark_source = ColumnDataSource(data={"x": dark_squares_x, "y": dark_squares_y})

p.rect(x="x", y="y", width=1, height=1, source=light_source, fill_color="#F0D9B5", line_color="#B58863", line_width=1)
p.rect(x="x", y="y", width=1, height=1, source=dark_source, fill_color="#B58863", line_color="#B58863", line_width=1)

# Add pieces using Label annotations with Unicode symbols
for square, piece in pieces.items():
    col = ord(square[0]) - ord("a")
    row = int(square[1]) - 1
    symbol = PIECE_SYMBOLS[piece]

    # White pieces get a slight shadow effect for visibility on light squares
    piece_color = "#1a1a1a" if piece.islower() else "#FFFFFF"

    # Add piece label
    label = Label(
        x=col,
        y=row,
        text=symbol,
        text_font_size="110pt",
        text_align="center",
        text_baseline="middle",
        text_color=piece_color,
        x_offset=0,
        y_offset=0,
    )
    p.add_layout(label)

# Add file labels (a-h)
files = "abcdefgh"
for i, f in enumerate(files):
    p.add_layout(
        Label(x=i, y=-0.3, text=f, text_font_size="36pt", text_align="center", text_baseline="top", text_color=INK_SOFT)
    )

# Add rank labels (1-8)
for i in range(8):
    p.add_layout(
        Label(
            x=-0.3,
            y=i,
            text=str(i + 1),
            text_font_size="36pt",
            text_align="right",
            text_baseline="middle",
            text_color=INK_SOFT,
        )
    )

# Style the plot
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.outline_line_width = 4

p.title.text_font_size = "48pt"
p.title.align = "center"
p.title.text_color = INK

# Hide axes and grid
p.axis.visible = False
p.grid.visible = False

# Add board border
p.rect(x=3.5, y=3.5, width=8, height=8, fill_alpha=0, line_color=INK_SOFT, line_width=8)

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome — Selenium 4 / Selenium Manager
W, H = 3600, 3600
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
