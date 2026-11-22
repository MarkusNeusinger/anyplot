""" anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (board squares and pieces follow chess convention instead)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
FILES = "abcdefgh"  # a chess board is always 8 x 8, white at the bottom
LIGHT_SQUARE = "#F0D9B5"
DARK_SQUARE = "#B58863"
# Solid glyphs (U+265A-F) are filled; outline glyphs (U+2654-59) are drawn on top as the rim
SOLID = {"k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"}
OUTLINE = {"k": "♔", "q": "♕", "r": "♖", "b": "♗", "n": "♘", "p": "♙"}

# Columns: set these to your table's column names
SQUARE = "square"  # role: square
PIECE = "piece"  # role: piece

# Data: replace this block with your own position, for example df = pd.read_csv("position.csv")
# Scholar's Mate: 1.e4 e5 2.Qh5 Nc6 3.Bc4 Nf6 4.Qxf7#
df = pd.DataFrame(
    {
        SQUARE: ["a1", "b1", "c1", "e1", "g1", "h1", "a2", "b2", "c2", "d2", "f2", "g2", "h2", "e4", "c4", "f7"]
        + ["a8", "c8", "d8", "e8", "f8", "h8", "a7", "b7", "c7", "d7", "g7", "h7", "e5", "c6", "f6"],
        PIECE: ["R", "N", "B", "K", "N", "R", "P", "P", "P", "P", "P", "P", "P", "P", "B", "Q"]
        + ["r", "b", "q", "k", "b", "r", "p", "p", "p", "p", "p", "p", "p", "n", "n"],
    }
)

# Plot: reads only df and the constants above
n = len(FILES)
squares = pd.DataFrame([(c, r) for r in range(n) for c in range(n)], columns=["x", "y"])
squares["color"] = ((squares["x"] + squares["y"]) % 2).map({1: LIGHT_SQUARE, 0: DARK_SQUARE})

pieces = df.assign(
    x=df[SQUARE].str[0].map(FILES.index),
    y=df[SQUARE].str[1:].astype(int) - 1,
    kind=df[PIECE].str.lower(),
    is_white=df[PIECE].str.isupper(),
)
pieces["solid"] = pieces["kind"].map(SOLID)
pieces["outline"] = pieces["kind"].map(OUTLINE)
pieces["fill"] = pieces["is_white"].map({True: "#FFFFFF", False: "#1A1A17"})
pieces["rim"] = "#1A1A17"

W, H = 2400, 2400
p = figure(
    width=W,
    height=H,
    title="Scholar's Mate · chessboard-pieces · python · bokeh · anyplot.ai",
    x_range=(-0.9, n - 0.5),
    y_range=(-0.9, n - 0.5),
    tools="",
    toolbar_location=None,
    min_border_left=40,
    min_border_right=40,
    min_border_top=110,
    min_border_bottom=40,
)

p.rect(x="x", y="y", width=1, height=1, source=ColumnDataSource(squares), fill_color="color", line_color=None)

piece_source = ColumnDataSource(pieces)
glyph_style = {"text_align": "center", "text_baseline": "middle", "text_font_size": "150pt", "source": piece_source}
p.text(x="x", y="y", text="solid", text_color="fill", **glyph_style)
p.text(x="x", y="y", text="outline", text_color="rim", **glyph_style)

# Board frame
p.rect(x=(n - 1) / 2, y=(n - 1) / 2, width=n, height=n, fill_alpha=0, line_color=INK_SOFT, line_width=6)

# File letters (a-h) below and rank numbers (1-8) left of the board
coords = pd.DataFrame({"i": range(n), "file": list(FILES), "rank": [str(i + 1) for i in range(n)]})
coord_source = ColumnDataSource(coords)
label_style = {"text_font_size": "34pt", "text_color": INK_SOFT, "text_baseline": "middle", "source": coord_source}
p.text(x="i", y=-0.75, text="file", text_align="center", **label_style)
p.text(x=-0.75, y="i", text="rank", text_align="center", **label_style)

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_alpha = 0
p.title.text_font_size = "40pt"
p.title.align = "center"
p.title.text_color = INK
p.axis.visible = False
p.grid.visible = False

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome — Selenium 4 / Selenium Manager
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
