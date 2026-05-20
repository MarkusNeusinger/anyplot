"""anyplot.ai
crossword-basic: Crossword Puzzle Grid
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-20
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
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Pygal style — carries theme tokens for consistent rendering
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
)

# Data — 15×15 crossword grid with 180° rotational symmetry
np.random.seed(42)
grid_size = 15
grid = np.zeros((grid_size, grid_size), dtype=int)

# Black cell positions for top half; mirror for 180° symmetry
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
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1
for r, c in black_positions_center:
    grid[r, c] = 1

# Clue numbers — cells that start an across or down word
numbers = {}
clue_num = 1
for row in range(grid_size):
    for col in range(grid_size):
        if grid[row, col] == 0:
            starts_across = (col == 0 or grid[row, col - 1] == 1) and (col < grid_size - 1 and grid[row, col + 1] == 0)
            starts_down = (row == 0 or grid[row - 1, col] == 1) and (row < grid_size - 1 and grid[row + 1, col] == 0)
            if starts_across or starts_down:
                numbers[(row, col)] = clue_num
                clue_num += 1

# SVG layout — 2400×2400 square canvas
CANVAS = 2400
CELL = 140  # 140 × 15 = 2100 px grid
GRID_W = CELL * grid_size  # 2100
GRID_X = (CANVAS - GRID_W) // 2  # 150 px side margin
GRID_Y = 200  # top area for title + gap
NUM_SZ = 28  # clue number font size (slightly larger per review)

title = "crossword-basic · python · pygal · anyplot.ai"

# Build SVG cell elements
cells = []
for row in range(grid_size):
    for col in range(grid_size):
        x = GRID_X + col * CELL
        y = GRID_Y + row * CELL
        fill = INK if grid[row, col] == 1 else ELEVATED_BG
        cells.append(
            f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}"'
            f' fill="{fill}" stroke="{INK_SOFT}" stroke-width="2"/>'
        )
        if (row, col) in numbers:
            cells.append(
                f'  <text x="{x + 6}" y="{y + NUM_SZ + 3}"'
                f' font-family="Arial, sans-serif" font-size="{NUM_SZ}"'
                f' fill="{INK}">{numbers[(row, col)]}</text>'
            )

cells_svg = "\n".join(cells)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
     width="{CANVAS}" height="{CANVAS}"
     viewBox="0 0 {CANVAS} {CANVAS}">
  <rect width="100%" height="100%" fill="{PAGE_BG}"/>
  <text x="{CANVAS // 2}" y="148"
        font-family="Arial, sans-serif" font-size="66" font-weight="bold"
        text-anchor="middle" fill="{INK}">{title}</text>
{cells_svg}
</svg>"""

# Save PNG (theme-suffixed)
cairosvg.svg2png(
    bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=CANVAS, output_height=CANVAS
)

# Save HTML with embedded interactive SVG
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      background: {PAGE_BG};
    }}
    svg {{ max-width: 95vw; max-height: 95vh; }}
  </style>
</head>
<body>{svg}</body>
</html>
"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html)
