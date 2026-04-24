""" anyplot.ai
sudoku-basic: Basic Sudoku Grid
Library: plotnine 0.15.3 | Python 3.14.4
Quality: 89/100 | Updated: 2026-04-24
"""

import os

import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_segment,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

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

# Build cell number DataFrame
cells = []
for row in range(9):
    for col in range(9):
        value = grid[row][col]
        cells.append({"x": col + 0.5, "y": 8.5 - row, "value": str(value) if value != 0 else ""})
df_cells = pd.DataFrame(cells)

# Thin grid lines (internal cell boundaries, skipping the 3x3 box positions)
thin_lines = []
for i in range(1, 9):
    if i % 3 != 0:
        thin_lines.append({"x": i, "xend": i, "y": 0, "yend": 9})
        thin_lines.append({"x": 0, "xend": 9, "y": i, "yend": i})
df_thin = pd.DataFrame(thin_lines)

# Thick grid lines (3x3 box boundaries and outer border)
thick_lines = []
for i in [0, 3, 6, 9]:
    thick_lines.append({"x": i, "xend": i, "y": 0, "yend": 9})
    thick_lines.append({"x": 0, "xend": 9, "y": i, "yend": i})
df_thick = pd.DataFrame(thick_lines)

# Cell background tiles (ensures panel fill matches theme uniformly across cells)
df_tiles = pd.DataFrame([{"x": col + 0.5, "y": row + 0.5} for row in range(9) for col in range(9)])

# Plot
plot = (
    ggplot()
    + geom_tile(data=df_tiles, mapping=aes(x="x", y="y"), fill=PAGE_BG, color="none", width=1, height=1)
    + geom_segment(
        data=df_thin, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=INK_MUTED, size=0.6, alpha=0.55
    )
    + geom_segment(data=df_thick, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=INK, size=2.4)
    + geom_text(data=df_cells, mapping=aes(x="x", y="y", label="value"), size=30, color=INK, fontweight="bold")
    + labs(title="sudoku-basic · plotnine · anyplot.ai")
    + coord_fixed(ratio=1, xlim=(-0.05, 9.05), ylim=(-0.05, 9.05))
    + theme_void()
    + theme(
        figure_size=(14, 14),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=26, ha="center", weight="bold", color=INK, margin={"b": 24}),
        plot_margin=0.04,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, width=14, height=14, verbose=False)
