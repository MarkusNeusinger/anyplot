""" pyplots.ai
sudoku-basic: Basic Sudoku Grid
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Sample Sudoku puzzle data (0 = empty cell)
grid = np.array(
    [
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
)

# Create cell data for tiles
cells = []
for row in range(9):
    for col in range(9):
        value = grid[row, col]
        cells.append(
            {
                "x": col + 0.5,
                "y": 8 - row + 0.5,  # Flip y to have row 0 at top
                "value": str(value) if value != 0 else "",
            }
        )

df_cells = pd.DataFrame(cells)

# Create data for thin grid lines (cell boundaries)
thin_lines = []
for i in range(10):
    if i % 3 != 0:  # Skip where thick lines go
        # Vertical line
        thin_lines.append({"x": i, "y": 0, "xend": i, "yend": 9, "group": f"v{i}"})
        # Horizontal line
        thin_lines.append({"x": 0, "y": i, "xend": 9, "yend": i, "group": f"h{i}"})

df_thin = pd.DataFrame(thin_lines)

# Create data for thick grid lines (3x3 box boundaries)
thick_lines = []
for i in [0, 3, 6, 9]:
    # Vertical line
    thick_lines.append({"x": i, "y": 0, "xend": i, "yend": 9, "group": f"v{i}"})
    # Horizontal line
    thick_lines.append({"x": 0, "y": i, "xend": 9, "yend": i, "group": f"h{i}"})

df_thick = pd.DataFrame(thick_lines)

# Build the plot
plot = (
    ggplot()
    # White background tiles for cells
    + geom_tile(aes(x="x", y="y"), data=df_cells, fill="white", color="white", width=1, height=1)
    # Thin lines for cell boundaries
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend", group="group"), data=df_thin, color="#666666", size=0.5)
    # Thick lines for 3x3 box boundaries
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend", group="group"), data=df_thick, color="black", size=2.5)
    # Numbers in cells
    + geom_text(aes(x="x", y="y", label="value"), data=df_cells, size=18, color="black", fontface="bold")
    # Styling
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=[-0.1, 9.1], expand=[0, 0])
    + scale_y_continuous(limits=[-0.1, 9.1], expand=[0, 0])
    + labs(title="sudoku-basic · letsplot · pyplots.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=24, hjust=0.5, face="bold"),
        plot_background=element_rect(fill="white"),
        panel_background=element_rect(fill="white"),
        plot_margin=[40, 40, 40, 40],
    )
    + ggsize(1200, 1200)  # Square format, scale 3x = 3600x3600
)

# Save outputs
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
