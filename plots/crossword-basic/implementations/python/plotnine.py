""" pyplots.ai
crossword-basic: Crossword Puzzle Grid
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Create 15x15 crossword grid with 180-degree rotational symmetry
np.random.seed(42)
size = 15

# Initialize grid (0 = white/entry, 1 = black/blocked)
grid = np.zeros((size, size), dtype=int)

# Create symmetric black cell pattern (traditional crossword style)
black_positions = [
    (0, 4),
    (0, 10),
    (1, 4),
    (1, 10),
    (2, 4),
    (2, 7),
    (2, 10),
    (3, 0),
    (3, 7),
    (3, 11),
    (3, 12),
    (3, 13),
    (3, 14),
    (4, 0),
    (4, 1),
    (4, 5),
    (4, 6),
    (4, 9),
    (5, 5),
    (5, 11),
    (6, 2),
    (6, 3),
    (6, 8),
    (6, 13),
    (6, 14),
    (7, 7),
]

# Apply black cells with 180-degree rotational symmetry
for r, c in black_positions:
    grid[r, c] = 1
    grid[size - 1 - r, size - 1 - c] = 1

# Create DataFrame for grid tiles
data = []
for r in range(size):
    for c in range(size):
        data.append(
            {
                "col": c + 1,
                "row": size - r,  # Flip for display (row 15 at top)
                "cell_type": "blocked" if grid[r, c] == 1 else "entry",
            }
        )

df = pd.DataFrame(data)

# Determine word start positions (cells that begin across or down words)
word_starts = {}
num = 1
for r in range(size):
    for c in range(size):
        if grid[r, c] == 1:
            continue
        starts_across = (c == 0 or grid[r, c - 1] == 1) and c < size - 1 and grid[r, c + 1] == 0
        starts_down = (r == 0 or grid[r - 1, c] == 1) and r < size - 1 and grid[r + 1, c] == 0
        if starts_across or starts_down:
            word_starts[(r, c)] = num
            num += 1

# Create DataFrame for clue numbers
number_data = []
for (r, c), clue_num in word_starts.items():
    number_data.append({"col": c + 1, "row": size - r, "label": str(clue_num)})

numbers_df = pd.DataFrame(number_data)

# Create the plot
plot = (
    ggplot(df, aes(x="col", y="row", fill="cell_type"))
    + geom_tile(color="#333333", size=0.5)
    + scale_fill_manual(values={"entry": "#FFFFFF", "blocked": "#1A1A1A"})
    + geom_text(
        data=numbers_df,
        mapping=aes(x="col", y="row", label="label"),
        size=7,
        ha="left",
        va="top",
        nudge_x=-0.35,
        nudge_y=0.35,
        color="#333333",
        inherit_aes=False,
    )
    + scale_x_continuous(breaks=[], expand=(0, 0))
    + scale_y_continuous(breaks=[], expand=(0, 0))
    + coord_fixed(ratio=1)
    + labs(title="crossword-basic · plotnine · pyplots.ai")
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        axis_text=element_blank(),
        axis_title=element_blank(),
        axis_ticks=element_blank(),
        panel_background=element_rect(fill="#E0E0E0"),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="none",
        plot_background=element_rect(fill="white"),
    )
)

# Save the plot
plot.save("plot.png", dpi=300, width=12, height=12)
