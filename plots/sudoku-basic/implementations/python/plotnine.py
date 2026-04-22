""" pyplots.ai
sudoku-basic: Basic Sudoku Grid
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_segment,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    theme,
    theme_void,
)


# Data - A valid partially filled Sudoku puzzle
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

# Convert grid to DataFrame for plotnine
cells = []
for row in range(9):
    for col in range(9):
        value = grid[row][col]
        cells.append(
            {
                "x": col + 0.5,
                "y": 8.5 - row,  # Flip y to have row 0 at top
                "value": str(value) if value != 0 else "",
            }
        )
df_cells = pd.DataFrame(cells)

# Create thin grid lines (all cell boundaries)
thin_lines = []
for i in range(10):
    # Skip positions where thick lines will be drawn
    if i % 3 != 0:
        # Vertical lines
        thin_lines.append({"x": i, "xend": i, "y": 0, "yend": 9})
        # Horizontal lines
        thin_lines.append({"x": 0, "xend": 9, "y": i, "yend": i})
df_thin = pd.DataFrame(thin_lines)

# Create thick grid lines (3x3 box boundaries)
thick_lines = []
for i in [0, 3, 6, 9]:
    # Vertical lines
    thick_lines.append({"x": i, "xend": i, "y": 0, "yend": 9})
    # Horizontal lines
    thick_lines.append({"x": 0, "xend": 9, "y": i, "yend": i})
df_thick = pd.DataFrame(thick_lines)

# Create tile data for cell backgrounds
df_tiles = pd.DataFrame([{"x": col + 0.5, "y": row + 0.5, "fill": "white"} for row in range(9) for col in range(9)])

# Build the plot
plot = (
    ggplot()
    # Cell backgrounds
    + geom_tile(data=df_tiles, mapping=aes(x="x", y="y"), fill="white", color="none", width=1, height=1)
    # Thin grid lines
    + geom_segment(data=df_thin, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#888888", size=0.5)
    # Thick grid lines for 3x3 boxes
    + geom_segment(data=df_thick, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="black", size=2)
    # Numbers in cells
    + geom_text(data=df_cells, mapping=aes(x="x", y="y", label="value"), size=28, color="black", fontweight="bold")
    # Title
    + labs(title="sudoku-basic · plotnine · pyplots.ai")
    # Fixed aspect ratio
    + coord_fixed(ratio=1, xlim=(0, 9), ylim=(0, 9))
    # Clean theme
    + theme_void()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", weight="bold", margin={"b": 20}),
        plot_background=element_blank(),
        panel_background=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, width=12, height=12, verbose=False)
