""" pyplots.ai
crossword-basic: Crossword Puzzle Grid
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-15
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Create a 15x15 crossword grid with 180-degree rotational symmetry
grid_size = 15

# Create symmetric black cell pattern (1 = blocked, 0 = entry)
grid = np.zeros((grid_size, grid_size), dtype=int)

# Define black cells (top-left half, then mirror for 180-degree symmetry)
black_positions = [
    (0, 4),
    (0, 10),
    (1, 4),
    (1, 10),
    (2, 7),
    (3, 0),
    (3, 1),
    (3, 6),
    (3, 11),
    (3, 12),
    (4, 5),
    (4, 9),
    (5, 3),
    (5, 8),
    (5, 13),
    (5, 14),
    (6, 2),
    (6, 7),
    (6, 12),
    (7, 6),
    (7, 8),
]

# Apply black cells with 180-degree rotational symmetry
for r, c in black_positions:
    grid[r, c] = 1
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1

# Generate clue numbers (inline check for word starts)
numbers = {}
clue_num = 1
for r in range(grid_size):
    for c in range(grid_size):
        if grid[r, c] == 1:  # Skip black cells
            continue
        # Check if cell starts an across word
        starts_across = (c == 0 or grid[r, c - 1] == 1) and (c < grid_size - 1 and grid[r, c + 1] == 0)
        # Check if cell starts a down word
        starts_down = (r == 0 or grid[r - 1, c] == 1) and (r < grid_size - 1 and grid[r + 1, c] == 0)
        if starts_across or starts_down:
            numbers[(r, c)] = clue_num
            clue_num += 1

# Prepare data for plotting
cells_data = []
for r in range(grid_size):
    for c in range(grid_size):
        cells_data.append(
            {
                "x": c,
                "y": grid_size - 1 - r,  # Flip y for proper orientation
                "blocked": grid[r, c],
            }
        )

df_cells = pd.DataFrame(cells_data)

# Prepare number labels
number_labels = []
for (r, c), num in numbers.items():
    number_labels.append(
        {
            "x": c + 0.05,
            "y": grid_size - 1 - r + 0.35,  # Position in top-left of cell
            "label": str(num),
        }
    )

df_numbers = pd.DataFrame(number_labels)

# Create the crossword plot
plot = (
    ggplot()
    # White cells (entry cells)
    + geom_tile(
        data=df_cells[df_cells["blocked"] == 0],
        mapping=aes(x="x", y="y"),
        fill="white",
        color="black",
        size=0.8,
        width=0.98,
        height=0.98,
    )
    # Black cells (blocked cells)
    + geom_tile(
        data=df_cells[df_cells["blocked"] == 1],
        mapping=aes(x="x", y="y"),
        fill="black",
        color="black",
        size=0.8,
        width=0.98,
        height=0.98,
    )
    # Clue numbers
    + geom_text(
        data=df_numbers,
        mapping=aes(x="x", y="y", label="label"),
        size=8,
        color="#306998",
        hjust=0,
        vjust=1,
        fontface="bold",
    )
    # Styling
    + coord_fixed(ratio=1)
    + labs(title="crossword-basic · letsplot · pyplots.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=28, hjust=0.5, face="bold"),
        plot_background=element_rect(fill="white"),
        panel_background=element_rect(fill="white"),
    )
    + ggsize(1200, 1200)  # Square format for crossword (3600x3600 at scale=3)
)

# Save as PNG (to current directory)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, "plot.html", path=".")
