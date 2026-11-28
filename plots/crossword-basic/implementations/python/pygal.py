"""anyplot.ai
crossword-basic: Crossword Puzzle Grid
Library: pygal 3.1.3 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
"""

import os as _os
import sys as _sys


# This file is named pygal.py — remove its directory from sys.path first so
# Python resolves `pygal` to the installed package, not this file itself.
_here = _os.path.abspath(_os.path.dirname(__file__))
_sys.path = [p for p in _sys.path if _os.path.abspath(p or ".") != _here]

import os

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Crossword paper stays a printed puzzle in both themes: light entry cells, solid black blocking cells
ENTRY_BG = "#FFFDF6"
BLOCK_BG = "#1A1A17" if THEME == "light" else "#0B0B09"
CELL_INK = "#1A1A17"
CELL_LINE = "#4A4A44" if THEME == "light" else "#6B6A63"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

CANVAS = 2400
CELL = 140
GRID_SIZE = 15
GRID_W = CELL * GRID_SIZE  # 2100 px — fills the plot area exactly
NUM_SZ = 28
MARGIN = 150  # equal margins on all sides around the 2100 px grid

TITLE = "crossword-basic · python · pygal · anyplot.ai"

# Pygal Style — applied to the chart for theme-consistent background, title, and chrome
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    guide_stroke_color=CELL_LINE,
    major_guide_stroke_color=CELL_LINE,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

# Data: replace this block with your own puzzle layout (grid of 0 = entry, 1 = blocked)
grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)

black_positions_top = [
    (0, 4),
    (0, 10),
    (1, 4),
    (1, 10),
    (2, 7),
    (3, 0),
    (3, 1),
    (3, 6),
    (4, 5),
    (4, 9),
    (5, 3),
    (5, 11),
    (6, 0),
    (6, 8),
    (6, 14),
]
black_positions_center = [(7, 2), (7, 7), (7, 12)]

for r, c in black_positions_top:
    grid[r, c] = 1
    grid[GRID_SIZE - 1 - r, GRID_SIZE - 1 - c] = 1
for r, c in black_positions_center:
    grid[r, c] = 1

# Clue numbering — cells that start an across or down word
numbers = {}
clue_num = 1
for row in range(GRID_SIZE):
    for col in range(GRID_SIZE):
        if grid[row, col] == 0:
            starts_across = (col == 0 or grid[row, col - 1] == 1) and (col < GRID_SIZE - 1 and grid[row, col + 1] == 0)
            starts_down = (row == 0 or grid[row - 1, col] == 1) and (row < GRID_SIZE - 1 and grid[row + 1, col] == 0)
            if starts_across or starts_down:
                numbers[(row, col)] = clue_num
                clue_num += 1

# Plot: pygal supplies the themed page and title; the cells go into its SVG tree
chart = pygal.XY(
    style=custom_style, width=CANVAS, height=CANVAS, title=TITLE, show_legend=False, margin=MARGIN, no_data_text=""
)
svg_text = chart.render(is_unicode=True)
parts = [f'<g transform="translate({MARGIN}, {MARGIN})">']
for row in range(GRID_SIZE):
    for col in range(GRID_SIZE):
        x, y = col * CELL, row * CELL
        fill = BLOCK_BG if grid[row, col] == 1 else ENTRY_BG
        parts.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{fill}" stroke="{CELL_LINE}" stroke-width="2"/>'
        )
        if (row, col) in numbers:
            parts.append(
                f'<text x="{x + 6}" y="{y + NUM_SZ + 3}" fill="{CELL_INK}" font-family="Arial, sans-serif" '
                f'font-size="{NUM_SZ}">{numbers[(row, col)]}</text>'
            )
parts.append("</g>")
svg_bytes = svg_text.replace("</svg>", "".join(parts) + "</svg>").encode("utf-8")

# Save: cairosvg converts the SVG to PNG, the same SVG is pygal's interactive output
cairosvg.svg2png(bytestring=svg_bytes, write_to=f"plot-{THEME}.png", output_width=CANVAS, output_height=CANVAS)
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(svg_bytes)
