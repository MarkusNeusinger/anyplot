""" pyplots.ai
sudoku-basic: Basic Sudoku Grid
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import plotly.graph_objects as go


# Data - Example Sudoku puzzle (0 = empty cell)
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

# Create figure
fig = go.Figure()

# Add cell numbers as text annotations
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
                    "font": {"size": 48, "color": "black", "family": "Arial Black"},
                    "showarrow": False,
                    "xanchor": "center",
                    "yanchor": "middle",
                }
            )

# Thin lines for individual cells
thin_lines_x = []
thin_lines_y = []
for i in range(10):
    if i % 3 != 0:  # Skip thick line positions
        # Vertical lines
        thin_lines_x.extend([i, i, None])
        thin_lines_y.extend([0, 9, None])
        # Horizontal lines
        thin_lines_x.extend([0, 9, None])
        thin_lines_y.extend([i, i, None])

fig.add_trace(
    go.Scatter(
        x=thin_lines_x,
        y=thin_lines_y,
        mode="lines",
        line={"color": "black", "width": 1.5},
        hoverinfo="skip",
        showlegend=False,
    )
)

# Thick lines for 3x3 box boundaries
thick_lines_x = []
thick_lines_y = []
for i in [0, 3, 6, 9]:
    # Vertical lines
    thick_lines_x.extend([i, i, None])
    thick_lines_y.extend([0, 9, None])
    # Horizontal lines
    thick_lines_x.extend([0, 9, None])
    thick_lines_y.extend([i, i, None])

fig.add_trace(
    go.Scatter(
        x=thick_lines_x,
        y=thick_lines_y,
        mode="lines",
        line={"color": "black", "width": 5},
        hoverinfo="skip",
        showlegend=False,
    )
)

# Update layout
fig.update_layout(
    title={
        "text": "sudoku-basic · plotly · pyplots.ai",
        "font": {"size": 36, "color": "black"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "range": [-0.5, 9.5],
        "scaleanchor": "y",
        "scaleratio": 1,
        "fixedrange": True,
    },
    yaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-0.5, 9.5], "fixedrange": True},
    plot_bgcolor="white",
    paper_bgcolor="white",
    annotations=annotations,
    margin={"l": 80, "r": 80, "t": 120, "b": 80},
)

# Save as PNG (square format for Sudoku grid)
fig.write_image("plot.png", width=1200, height=1200, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
