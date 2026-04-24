""" anyplot.ai
sudoku-basic: Basic Sudoku Grid
Library: bokeh 3.9.0 | Python 3.14.4
Quality: 87/100 | Updated: 2026-04-24
"""

import os

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Data - 9x9 Sudoku puzzle (0 = empty); every digit 1-9 appears 3-5 times
grid = [
    [0, 0, 0, 2, 6, 0, 7, 0, 1],
    [6, 8, 0, 0, 7, 0, 0, 9, 0],
    [1, 9, 0, 0, 0, 4, 5, 0, 0],
    [8, 2, 0, 1, 0, 0, 0, 4, 0],
    [0, 0, 4, 6, 0, 2, 9, 0, 0],
    [0, 5, 0, 0, 0, 3, 0, 2, 8],
    [0, 0, 9, 3, 0, 0, 0, 7, 4],
    [0, 4, 0, 0, 5, 0, 0, 3, 6],
    [7, 0, 3, 0, 1, 8, 0, 0, 0],
]

# Build ColumnDataSource for non-empty cell numbers (row 0 at top)
number_rows = {"x": [], "y": [], "text": []}
for row in range(9):
    for col in range(9):
        value = grid[row][col]
        if value != 0:
            number_rows["x"].append(col + 0.5)
            number_rows["y"].append(8 - row + 0.5)
            number_rows["text"].append(str(value))
numbers = ColumnDataSource(number_rows)

# Build ColumnDataSources for thin cell lines and thick 3x3 box lines
thin_rows = {"x0": [], "y0": [], "x1": [], "y1": []}
for i in range(10):
    thin_rows["x0"].extend([0, i])
    thin_rows["y0"].extend([i, 0])
    thin_rows["x1"].extend([9, i])
    thin_rows["y1"].extend([i, 9])
thin_lines = ColumnDataSource(thin_rows)

thick_rows = {"x0": [], "y0": [], "x1": [], "y1": []}
for i in range(0, 10, 3):
    thick_rows["x0"].extend([0, i])
    thick_rows["y0"].extend([i, 0])
    thick_rows["x1"].extend([9, i])
    thick_rows["y1"].extend([i, 9])
thick_lines = ColumnDataSource(thick_rows)

# Plot - square 3600x3600 for a symmetric grid
p = figure(
    width=3600,
    height=3600,
    x_range=(-0.25, 9.25),
    y_range=(-0.25, 9.25),
    title="sudoku-basic · bokeh · anyplot.ai",
    tools="",
    toolbar_location=None,
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
)

p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=thin_lines, line_width=3, line_color=INK)
p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=thick_lines, line_width=10, line_color=INK)

p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=numbers,
        text_font_size="60pt",
        text_font_style="bold",
        text_align="center",
        text_baseline="middle",
        text_color=INK,
    )
)

# Style
p.title.text_font_size = "48pt"
p.title.align = "center"
p.title.text_font_style = "bold"
p.title.text_color = INK
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html", title="sudoku-basic · bokeh · anyplot.ai")
save(p)
