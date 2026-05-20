"""anyplot.ai
crossword-basic: Crossword Puzzle Grid
Library: plotly | Python 3.13
Quality: 91/100 | Updated: 2026-05-20
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Crossword cell colors — fixed regardless of theme (contrast IS the data)
CELL_ENTRY = "#FFFFFF"
CELL_BLOCK = "#1A1A17"

# Data - 15x15 crossword grid with 180-degree rotational symmetry
np.random.seed(42)
grid_size = 15

grid = np.zeros((grid_size, grid_size), dtype=int)

black_cells = [
    (0, 4),
    (0, 10),
    (1, 4),
    (1, 10),
    (2, 7),
    (3, 0),
    (3, 1),
    (3, 8),
    (3, 9),
    (4, 5),
    (4, 11),
    (4, 12),
    (4, 13),
    (4, 14),
    (5, 3),
    (5, 6),
    (6, 2),
    (6, 9),
    (6, 10),
    (7, 0),
    (7, 7),
    (7, 14),
]

for r, c in black_cells:
    grid[r, c] = 1
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1

# Generate clue numbers (cells that start across or down words)
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

# Plot
fig = go.Figure()

cell_size = 1
for r in range(grid_size):
    for c in range(grid_size):
        x0, y0 = c * cell_size, (grid_size - 1 - r) * cell_size
        x1, y1 = x0 + cell_size, y0 + cell_size

        fill_color = CELL_BLOCK if grid[r, c] == 1 else CELL_ENTRY

        fig.add_shape(
            type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=fill_color, line=dict(color=INK_SOFT, width=1.5)
        )

# Clue numbers — slightly larger than previous for better visibility
for (r, c), num in numbers.items():
    x = c * cell_size + 0.07
    y = (grid_size - 1 - r) * cell_size + cell_size - 0.07

    fig.add_annotation(
        x=x,
        y=y,
        text=str(num),
        showarrow=False,
        font=dict(size=11, color="#1A1A17", family="Arial"),
        xanchor="left",
        yanchor="top",
    )

# Style
fig.update_layout(
    title=dict(
        text="crossword-basic · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        showgrid=False,
        zeroline=False,
        showticklabels=False,
        scaleanchor="y",
        scaleratio=1,
        range=[-0.3, grid_size + 0.3],
    ),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.3, grid_size + 0.3]),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    margin=dict(l=50, r=50, t=90, b=50),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
