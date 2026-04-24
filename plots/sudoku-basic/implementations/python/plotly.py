""" anyplot.ai
sudoku-basic: Basic Sudoku Grid
Library: plotly 6.7.0 | Python 3.14.4
Quality: 90/100 | Updated: 2026-04-24
"""

import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - A partially filled Sudoku puzzle (0 = empty cell)
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

# Figure
fig = go.Figure()

# Cell numbers as annotations
annotations = []
for row in range(9):
    for col in range(9):
        value = grid[row][col]
        if value != 0:
            annotations.append(
                {
                    "x": col + 0.5,
                    "y": 8 - row + 0.5,
                    "text": str(value),
                    "font": {"size": 48, "color": INK, "family": "Arial Black"},
                    "showarrow": False,
                    "xanchor": "center",
                    "yanchor": "middle",
                }
            )

# Thin lines for individual cell boundaries
thin_lines_x = []
thin_lines_y = []
for i in range(10):
    if i % 3 != 0:
        thin_lines_x.extend([i, i, None, 0, 9, None])
        thin_lines_y.extend([0, 9, None, i, i, None])

fig.add_trace(
    go.Scatter(
        x=thin_lines_x,
        y=thin_lines_y,
        mode="lines",
        line={"color": INK, "width": 2},
        hoverinfo="skip",
        showlegend=False,
    )
)

# Thick lines for 3x3 box boundaries
thick_lines_x = []
thick_lines_y = []
for i in [0, 3, 6, 9]:
    thick_lines_x.extend([i, i, None, 0, 9, None])
    thick_lines_y.extend([0, 9, None, i, i, None])

fig.add_trace(
    go.Scatter(
        x=thick_lines_x,
        y=thick_lines_y,
        mode="lines",
        line={"color": INK, "width": 6},
        hoverinfo="skip",
        showlegend=False,
    )
)

# Invisible hover layer for cell coordinates (HTML interactivity)
hover_x = [c + 0.5 for r in range(9) for c in range(9)]
hover_y = [8 - r + 0.5 for r in range(9) for c in range(9)]
hover_text = [
    f"R{r + 1}C{c + 1}" + (f" = {grid[r][c]}" if grid[r][c] != 0 else " (empty)") for r in range(9) for c in range(9)
]
fig.add_trace(
    go.Scatter(
        x=hover_x,
        y=hover_y,
        mode="markers",
        marker={"size": 60, "color": "rgba(0,0,0,0)"},
        hovertext=hover_text,
        hoverinfo="text",
        showlegend=False,
    )
)

# Layout
fig.update_layout(
    title={
        "text": "sudoku-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "range": [-0.3, 9.3],
        "scaleanchor": "y",
        "scaleratio": 1,
        "fixedrange": True,
    },
    yaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-0.3, 9.3], "fixedrange": True},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK_SOFT},
    annotations=annotations,
    margin={"l": 60, "r": 60, "t": 100, "b": 60},
)

# Save (square 1:1 format suits a 9x9 grid)
fig.write_image(f"plot-{THEME}.png", width=1200, height=1200, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
