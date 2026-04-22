""" pyplots.ai
sudoku-basic: Basic Sudoku Grid
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

from bokeh.io import export_png
from bokeh.models import Label
from bokeh.plotting import figure, output_file, save


# Data - a partially filled Sudoku puzzle
grid = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

# Create figure - square 3600x3600 for symmetric grid
p = figure(
    width=3600,
    height=3600,
    x_range=(-0.5, 9.5),
    y_range=(-0.5, 9.5),
    title="sudoku-basic · bokeh · pyplots.ai",
    tools="",
    toolbar_location=None,
)

# Style the figure
p.title.text_font_size = "48pt"
p.title.align = "center"
p.title.text_font_style = "bold"

# Remove axes
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Background
p.background_fill_color = "white"

# Draw thin grid lines (individual cells)
for i in range(10):
    # Horizontal lines
    p.line(x=[-0.02, 9.02], y=[i, i], line_width=3, line_color="black")
    # Vertical lines
    p.line(x=[i, i], y=[-0.02, 9.02], line_width=3, line_color="black")

# Draw thick box boundary lines (3x3 boxes)
for i in range(0, 10, 3):
    # Horizontal thick lines
    p.line(x=[-0.02, 9.02], y=[i, i], line_width=10, line_color="black")
    # Vertical thick lines
    p.line(x=[i, i], y=[-0.02, 9.02], line_width=10, line_color="black")

# Add numbers to cells
for row in range(9):
    for col in range(9):
        value = grid[row][col]
        if value != 0:
            # y-axis is flipped (row 0 at top)
            x_pos = col + 0.5
            y_pos = 8 - row + 0.5
            label = Label(
                x=x_pos,
                y=y_pos,
                text=str(value),
                text_font_size="60pt",
                text_font_style="bold",
                text_align="center",
                text_baseline="middle",
                text_color="black",
            )
            p.add_layout(label)

# Save as PNG and HTML
export_png(p, filename="plot.png")
output_file("plot.html", title="sudoku-basic · bokeh · pyplots.ai")
save(p)
