""" anyplot.ai
crossword-basic: Crossword Puzzle Grid
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-20
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Data — 15x15 crossword grid with 180-degree rotational symmetry
grid_size = 15
grid = np.zeros((grid_size, grid_size), dtype=int)

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

for r, c in black_positions:
    grid[r, c] = 1
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1

# Generate clue numbers
numbers = {}
clue_num = 1
for r in range(grid_size):
    for c in range(grid_size):
        if grid[r, c] == 1:
            continue
        starts_across = (c == 0 or grid[r, c - 1] == 1) and (c < grid_size - 1 and grid[r, c + 1] == 0)
        starts_down = (r == 0 or grid[r - 1, c] == 1) and (r < grid_size - 1 and grid[r + 1, c] == 0)
        if starts_across or starts_down:
            numbers[(r, c)] = clue_num
            clue_num += 1

# Prepare cell data
cells_data = []
for r in range(grid_size):
    for c in range(grid_size):
        cell_type = "Blocked" if grid[r, c] == 1 else "Entry"
        cells_data.append({"x": c, "y": grid_size - 1 - r, "blocked": grid[r, c], "cell_type": cell_type})

df_cells = pd.DataFrame(cells_data)

# Prepare number labels with tooltip info
number_labels = []
for (r, c), num in numbers.items():
    direction_parts = []
    starts_across = (c == 0 or grid[r, c - 1] == 1) and (c < grid_size - 1 and grid[r, c + 1] == 0)
    starts_down = (r == 0 or grid[r - 1, c] == 1) and (r < grid_size - 1 and grid[r + 1, c] == 0)
    if starts_across:
        direction_parts.append("Across")
    if starts_down:
        direction_parts.append("Down")
    number_labels.append(
        {
            "x": c + 0.05,
            "y": grid_size - 1 - r + 0.35,
            "label": str(num),
            "clue": f"Clue {num}: {' / '.join(direction_parts)}",
        }
    )

df_numbers = pd.DataFrame(number_labels)

# Plot
plot = (
    ggplot()
    + geom_tile(
        data=df_cells[df_cells["blocked"] == 0],
        mapping=aes(x="x", y="y"),
        fill="white",
        color="black",
        size=0.8,
        width=0.98,
        height=0.98,
        tooltips=layer_tooltips().line("@cell_type cell"),
    )
    + geom_tile(
        data=df_cells[df_cells["blocked"] == 1],
        mapping=aes(x="x", y="y"),
        fill="black",
        color="black",
        size=0.8,
        width=0.98,
        height=0.98,
        tooltips=layer_tooltips().line("@cell_type cell"),
    )
    + geom_text(
        data=df_numbers,
        mapping=aes(x="x", y="y", label="label"),
        size=8,
        color=INK,
        hjust=0,
        vjust=1,
        fontface="bold",
        tooltips=layer_tooltips().line("@clue"),
    )
    + coord_fixed(ratio=1)
    + labs(title="crossword-basic · python · letsplot · anyplot.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=16, hjust=0.5, face="bold", color=INK),
        plot_background=element_rect(fill=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
    + ggsize(600, 600)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
