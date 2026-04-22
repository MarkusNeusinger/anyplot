""" pyplots.ai
chessboard-basic: Chess Board Grid Visualization
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import pygal
from pygal.style import Style


# Chess board configuration
columns = ["a", "b", "c", "d", "e", "f", "g", "h"]

# Classic chess board colors
light_color = "#F0D9B5"  # Cream/tan for light squares
dark_color = "#B58863"  # Brown for dark squares

# Create the board using stacked bars
# Each row is a horizontal bar with 8 stacked colored segments
board = pygal.StackedBar(
    style=Style(
        background="#FFFFFF",
        plot_background="#FFFFFF",
        foreground="#333333",
        foreground_strong="#333333",
        foreground_subtle="#555555",
        title_font_size=72,
        label_font_size=52,
        major_label_font_size=48,
        legend_font_size=0,
        value_font_size=0,
        font_family="Arial",
        opacity=1.0,
        opacity_hover=1.0,
        transition="0s",
    ),
    width=3600,
    height=3600,
    title="chessboard-basic · pygal · pyplots.ai",
    show_legend=False,
    show_y_guides=False,
    show_x_guides=False,
    spacing=0,
    margin=180,
    margin_left=220,
    print_values=False,
    truncate_label=-1,
    y_labels=[1, 2, 3, 4, 5, 6, 7, 8],
    min_scale=1,
)

# X-axis labels (columns a-h at bottom)
board.x_labels = columns

# For StackedBar, each add() creates a layer in the stack
# We need 8 layers, each representing one "row" of the chessboard
# The first add() is at the bottom, last at top

# Build data for each row from row 1 (bottom) to row 8 (top)
for row_num in range(1, 9):
    row_data = []
    for col_idx in range(8):
        # Standard chess: a1 is dark (col_idx=0, row=1: 0+1=1 odd -> dark)
        # h1 is light (col_idx=7, row=1: 7+1=8 even -> light)
        is_light = (col_idx + row_num) % 2 == 0

        color = light_color if is_light else dark_color
        row_data.append({"value": 1, "color": color})

    board.add(str(row_num), row_data)

# Render to files
board.render_to_file("plot.svg")
board.render_to_png("plot.png")
board.render_to_file("plot.html")
