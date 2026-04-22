""" pyplots.ai
crossword-basic: Crossword Puzzle Grid
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import numpy as np
import plotly.graph_objects as go


# Data - 15x15 crossword grid with 180-degree rotational symmetry
np.random.seed(42)
grid_size = 15

# Create a symmetric crossword pattern
# 0 = white cell (letter entry), 1 = black cell (blocked)
grid = np.zeros((grid_size, grid_size), dtype=int)

# Define black cells for top-left quadrant + center row/column (will mirror for symmetry)
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

# Apply black cells with 180-degree rotational symmetry
for r, c in black_cells:
    grid[r, c] = 1
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1

# Generate clue numbers - cells that start words (across or down)
numbers = {}
clue_num = 1

for r in range(grid_size):
    for c in range(grid_size):
        if grid[r, c] == 1:
            continue

        # Check if this cell starts an across word (left is edge or black, right is white)
        starts_across = (c == 0 or grid[r, c - 1] == 1) and (c < grid_size - 1 and grid[r, c + 1] == 0)

        # Check if this cell starts a down word (top is edge or black, bottom is white)
        starts_down = (r == 0 or grid[r - 1, c] == 1) and (r < grid_size - 1 and grid[r + 1, c] == 0)

        if starts_across or starts_down:
            numbers[(r, c)] = clue_num
            clue_num += 1

# Create figure
fig = go.Figure()

# Draw cells
cell_size = 1
for r in range(grid_size):
    for c in range(grid_size):
        x0, y0 = c * cell_size, (grid_size - 1 - r) * cell_size
        x1, y1 = x0 + cell_size, y0 + cell_size

        # Cell color
        fill_color = "#000000" if grid[r, c] == 1 else "#FFFFFF"

        # Add cell rectangle
        fig.add_shape(
            type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=fill_color, line=dict(color="#306998", width=2)
        )

# Add clue numbers to cells
for (r, c), num in numbers.items():
    x = c * cell_size + 0.08
    y = (grid_size - 1 - r) * cell_size + cell_size - 0.08

    fig.add_annotation(
        x=x,
        y=y,
        text=str(num),
        showarrow=False,
        font=dict(size=14, color="#306998", family="Arial Black"),
        xanchor="left",
        yanchor="top",
    )

# Layout
fig.update_layout(
    title=dict(
        text="crossword-basic · plotly · pyplots.ai", font=dict(size=28, color="#306998"), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        showgrid=False,
        zeroline=False,
        showticklabels=False,
        scaleanchor="y",
        scaleratio=1,
        range=[-0.5, grid_size + 0.5],
    ),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, grid_size + 0.5]),
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=50, r=50, t=100, b=50),
    width=1200,
    height=1200,
)

# Save outputs
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html")
