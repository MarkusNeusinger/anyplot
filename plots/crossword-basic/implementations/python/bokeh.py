""" pyplots.ai
crossword-basic: Crossword Puzzle Grid
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-15
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure


# Data - Create a 15x15 crossword grid with symmetric black cells
np.random.seed(42)
grid_size = 15

# Create symmetric black cell pattern (180-degree rotational symmetry)
# Start with a template and mirror it
grid = np.zeros((grid_size, grid_size), dtype=int)

# Add black cells in one half (will be mirrored)
black_positions = [
    (0, 4),
    (0, 10),
    (1, 4),
    (1, 10),
    (2, 7),
    (3, 0),
    (3, 6),
    (3, 11),
    (3, 12),
    (4, 5),
    (4, 9),
    (5, 3),
    (5, 8),
    (5, 13),
    (6, 2),
    (6, 7),
    (6, 12),
    (7, 0),
    (7, 6),
    (7, 8),
    (7, 14),
]

# Place black cells and their symmetric counterparts
for r, c in black_positions:
    grid[r, c] = 1
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1

# Calculate clue numbers (cells that start across or down words)
numbers = {}
clue_num = 1

for r in range(grid_size):
    for c in range(grid_size):
        if grid[r, c] == 1:
            continue

        # Check if this cell starts an across word
        starts_across = (c == 0 or grid[r, c - 1] == 1) and (c < grid_size - 1 and grid[r, c + 1] == 0)

        # Check if this cell starts a down word
        starts_down = (r == 0 or grid[r - 1, c] == 1) and (r < grid_size - 1 and grid[r + 1, c] == 0)

        if starts_across or starts_down:
            numbers[(r, c)] = clue_num
            clue_num += 1

# Prepare data for bokeh
white_x, white_y = [], []
black_x, black_y = [], []

for r in range(grid_size):
    for c in range(grid_size):
        # Flip y-coordinate so row 0 is at top
        y = grid_size - 1 - r
        if grid[r, c] == 0:
            white_x.append(c)
            white_y.append(y)
        else:
            black_x.append(c)
            black_y.append(y)

# Create figure - Square format for crossword (3600x3600)
p = figure(
    width=3600,
    height=3600,
    title="crossword-basic · bokeh · pyplots.ai",
    x_range=(-0.6, grid_size - 0.4),
    y_range=(-0.6, grid_size - 0.4),
    tools="",
    toolbar_location=None,
)

# Remove axes and grid for clean puzzle look
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Style the title
p.title.text_font_size = "48pt"
p.title.align = "center"

# Draw white cells as squares with borders
white_source = ColumnDataSource(data={"x": white_x, "y": white_y})
p.rect(
    x="x", y="y", source=white_source, width=0.98, height=0.98, fill_color="white", line_color="#333333", line_width=2
)

# Draw black cells as filled squares
black_source = ColumnDataSource(data={"x": black_x, "y": black_y})
p.rect(
    x="x", y="y", source=black_source, width=0.98, height=0.98, fill_color="#1a1a1a", line_color="#1a1a1a", line_width=2
)

# Add clue numbers to cells
for (r, c), num in numbers.items():
    y = grid_size - 1 - r
    label = Label(
        x=c - 0.42, y=y + 0.2, text=str(num), text_font_size="16pt", text_font_style="bold", text_color="#333333"
    )
    p.add_layout(label)

# Set background color
p.background_fill_color = "#f5f5f5"
p.border_fill_color = "#f5f5f5"
p.outline_line_color = None

# Save as PNG and HTML
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
