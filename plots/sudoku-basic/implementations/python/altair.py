""" pyplots.ai
sudoku-basic: Basic Sudoku Grid
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import altair as alt
import pandas as pd


# Sudoku puzzle data (0 = empty cell)
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

# Build data for cells with numbers
cell_data = []
for row in range(9):
    for col in range(9):
        value = grid[row][col]
        if value != 0:
            cell_data.append({"col": col + 0.5, "row": 8 - row + 0.5, "value": str(value)})

df_numbers = pd.DataFrame(cell_data)

# Build grid lines data
thin_lines = []
thick_lines = []

# Vertical lines
for i in range(10):
    line = {"x": i, "x2": i, "y": 0, "y2": 9}
    if i % 3 == 0:
        thick_lines.append(line)
    else:
        thin_lines.append(line)

# Horizontal lines
for i in range(10):
    line = {"x": 0, "x2": 9, "y": i, "y2": i}
    if i % 3 == 0:
        thick_lines.append(line)
    else:
        thin_lines.append(line)

df_thin = pd.DataFrame(thin_lines)
df_thick = pd.DataFrame(thick_lines)

# Create thin grid lines
thin_grid = alt.Chart(df_thin).mark_rule(color="black", strokeWidth=1).encode(x="x:Q", x2="x2:Q", y="y:Q", y2="y2:Q")

# Create thick grid lines (3x3 box boundaries)
thick_grid = alt.Chart(df_thick).mark_rule(color="black", strokeWidth=4).encode(x="x:Q", x2="x2:Q", y="y:Q", y2="y2:Q")

# Create number labels
numbers = (
    alt.Chart(df_numbers)
    .mark_text(fontSize=48, fontWeight="bold", color="black")
    .encode(x="col:Q", y="row:Q", text="value:N")
)

# Combine layers
chart = (
    alt.layer(thin_grid, thick_grid, numbers)
    .properties(width=900, height=900, title=alt.Title("sudoku-basic · altair · pyplots.ai", fontSize=32))
    .configure_axis(grid=False, domain=False, ticks=False, labels=False, title=None)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=4.0)
chart.save("plot.html")
