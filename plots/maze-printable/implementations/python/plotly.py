"""anyplot.ai
maze-printable: Printable Maze Puzzle
Library: plotly 6.7.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-16
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Imprint palette: position 1 marks start and goal
BRAND = "#009E73"

# Data: maze parameters; replace these to get a different puzzle
WIDTH = 25  # cells horizontally
HEIGHT = 25  # cells vertically
SEED = 42

rng = np.random.default_rng(SEED)

# Grid of 2*n+1 tiles per axis: odd tiles are cells, even tiles are walls (True = wall)
maze = np.ones((2 * HEIGHT + 1, 2 * WIDTH + 1), dtype=bool)
maze[1::2, 1::2] = False

# Depth-first carving: a spanning tree of cells, so exactly one route joins any two cells
visited = np.zeros((HEIGHT, WIDTH), dtype=bool)
visited[0, 0] = True
stack = [(0, 0)]
while stack:
    cy, cx = stack[-1]
    options = [
        (cy + dy, cx + dx, dy, dx)
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0))
        if 0 <= cy + dy < HEIGHT and 0 <= cx + dx < WIDTH and not visited[cy + dy, cx + dx]
    ]
    if options:
        ny, nx, dy, dx = options[rng.integers(len(options))]
        maze[2 * cy + 1 + dy, 2 * cx + 1 + dx] = False
        visited[ny, nx] = True
        stack.append((ny, nx))
    else:
        stack.pop()

# Entrance above the first cell, exit below the last cell
maze[0, 1] = False
maze[-1, -2] = False

# Plot
rows, cols = maze.shape

# All wall tiles as one SVG path; row 0 is drawn at the top
tiles = [
    f"M{x - 0.5},{rows - 1.5 - y}L{x + 0.5},{rows - 1.5 - y}L{x + 0.5},{rows - 0.5 - y}L{x - 0.5},{rows - 0.5 - y}Z"
    for y, x in zip(*np.nonzero(maze), strict=True)
]

fig = go.Figure()
fig.add_annotation(
    x=1,
    y=rows - 1,
    text="<b>START</b>",
    font={"size": 15, "color": BRAND},
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2.5,
    arrowcolor=BRAND,
    ax=0,
    ay=-30,
    yanchor="bottom",
)
fig.add_annotation(
    x=cols - 2,
    y=0,
    text="<b>GOAL</b>",
    font={"size": 15, "color": BRAND},
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2.5,
    arrowcolor=BRAND,
    ax=0,
    ay=30,
    yanchor="top",
)

fig.update_layout(
    title={
        "text": "maze-printable · python · plotly · anyplot.ai",
        "font": {"size": 17, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    shapes=[{"type": "path", "path": "".join(tiles), "fillcolor": INK, "line": {"width": 0}}],
    xaxis={"visible": False, "range": [-1.5, cols + 0.5], "scaleanchor": "y", "scaleratio": 1, "constrain": "domain"},
    yaxis={"visible": False, "range": [-5, rows + 4], "constrain": "domain"},
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    autosize=False,
    margin={"l": 40, "r": 40, "t": 60, "b": 30},
    width=600,
    height=600,
)

fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
