""" anyplot.ai
crossword-basic: Crossword Puzzle Grid
Library: pygal 3.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-20
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
from pygal.graph.graph import Graph
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

CANVAS = 2400
CELL = 140
GRID_SIZE = 15
GRID_W = CELL * GRID_SIZE  # 2100 px — fills the plot area exactly
NUM_SZ = 28

TITLE = "crossword-basic · python · pygal · anyplot.ai"

# Pygal Style — applied to the chart for theme-consistent background, title, and chrome
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

# Crossword grid data — 15×15 with 180° rotational symmetry
np.random.seed(42)
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


class CrosswordGrid(Graph):
    """Custom pygal chart type that renders a crossword puzzle grid.

    Subclasses Graph to use pygal's SVG infrastructure (style, background,
    title, render pipeline) while drawing grid cells via pygal's SVG node API.
    """

    def _compute(self):
        pass

    def _compute_x_labels(self):
        pass

    def _compute_y_labels(self):
        pass

    def _draw(self):
        """Draw chart elements; always calls _plot since no series data is needed."""
        self._compute()
        self._compute_x_labels()
        self._compute_x_labels_major()
        self._compute_y_labels()
        self._compute_y_labels_major()
        self._compute_secondary()
        self._post_compute()
        self._compute_margin()
        self._decorate()
        self._plot()

    def _plot(self):
        """Render crossword cells using pygal's SVG node API.

        Coordinates are relative to the plot group (margin already applied),
        so (0, 0) maps to the top-left corner of the grid area on the canvas.
        """
        plot = self.nodes["plot"]
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = col * CELL
                y = row * CELL
                fill = INK if grid[row, col] == 1 else ELEVATED_BG

                rect = self.svg.node(plot, "rect", x=x, y=y, width=CELL, height=CELL, fill=fill)
                rect.set("stroke", INK_SOFT)
                rect.set("stroke-width", "2")

                if (row, col) in numbers:
                    txt = self.svg.node(plot, "text", x=x + 6, y=y + NUM_SZ + 3, fill=INK)
                    txt.set("font-family", "Arial, sans-serif")
                    txt.set("font-size", str(NUM_SZ))
                    txt.text = str(numbers[(row, col)])


# margin=150 → equal 150 px margins on all sides; plot area = 2100×2100 = grid size
chart = CrosswordGrid(style=custom_style, width=CANVAS, height=CANVAS, title=TITLE, show_legend=False, margin=150)

# Render via pygal's pipeline: render() produces the SVG, cairosvg converts to PNG
svg_bytes = chart.render()
cairosvg.svg2png(bytestring=svg_bytes, write_to=f"plot-{THEME}.png", output_width=CANVAS, output_height=CANVAS)

# HTML: pygal's interactive SVG output (embedded in a minimal page)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(chart.render(is_unicode=True))
