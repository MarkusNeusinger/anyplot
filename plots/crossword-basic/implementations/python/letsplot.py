"""anyplot.ai
crossword-basic: Crossword Puzzle Grid
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
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

# Constants
CELL_FILLS = ["white", "black"]  # entry cells, then blocking cells (monochrome, print-oriented)

# Columns: set these to your table's column names
COLUMN = "Column"  # role: grid
ROW = "Row"  # role: extra
BLOCKED = "Blocked"  # role: extra
CLUE = "Clue number"  # role: numbers
CELL = "Cell type"  # role: extra
DIRECTION = "Direction"  # role: extra

# Data: replace this block with your own table, one row per grid cell, for example df = pd.read_csv("grid.csv")
# 15x15 crossword with 180-degree rotational symmetry; clue numbers follow the across/down word starts
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

rows = []
clue_num = 0
for r in range(grid_size):
    for c in range(grid_size):
        starts_across = (
            grid[r, c] == 0 and (c == 0 or grid[r, c - 1] == 1) and (c < grid_size - 1 and grid[r, c + 1] == 0)
        )
        starts_down = (
            grid[r, c] == 0 and (r == 0 or grid[r - 1, c] == 1) and (r < grid_size - 1 and grid[r + 1, c] == 0)
        )
        if starts_across or starts_down:
            clue_num += 1
        rows.append(
            {
                COLUMN: c,
                ROW: r,
                BLOCKED: int(grid[r, c]),
                CLUE: clue_num if (starts_across or starts_down) else 0,
                CELL: "Blocked" if grid[r, c] == 1 else "Entry",
                DIRECTION: " / ".join(
                    name for name, starts in (("Across", starts_across), ("Down", starts_down)) if starts
                ),
            }
        )
df = pd.DataFrame(rows)

# Plot
numbered = df[df[CLUE] > 0].assign(label=lambda d: d[CLUE].astype(str))
n_cols = df[COLUMN].nunique()
n_rows = df[ROW].nunique()

grid_plot = (
    ggplot(df, aes(x=COLUMN, y=ROW))
    + geom_tile(
        aes(fill=as_discrete(BLOCKED)),
        color="black",
        size=0.8,
        width=0.98,
        height=0.98,
        tooltips=layer_tooltips().line(f"@{{{CELL}}} cell"),
    )
    + geom_text(
        data=numbered,
        mapping=aes(x=COLUMN, y=ROW, label="label"),
        position=position_nudge(x=-0.44, y=0.44),
        size=4.2,
        color="#1A1A17",
        hjust=0,
        vjust=1,
        fontface="bold",
        tooltips=layer_tooltips().line(f"Clue @{{{CLUE}}}: @{{{DIRECTION}}}"),
    )
    + scale_fill_manual(values=CELL_FILLS)
    + scale_y_reverse()
    + coord_fixed(ratio=1, xlim=[-0.5, n_cols - 0.5], ylim=[-0.5, n_rows - 0.5])
    + labs(title="crossword-basic · python · letsplot · anyplot.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=16, hjust=0.5, face="bold", color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        legend_position="none",
    )
)

# The one-panel grid paints the page color across the whole canvas
plot = (
    gggrid([grid_plot])
    + ggsize(600, 600)
    + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG), plot_title=element_text(color=INK))
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
