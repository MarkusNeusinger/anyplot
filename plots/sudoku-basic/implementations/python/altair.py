""" anyplot.ai
sudoku-basic: Basic Sudoku Grid
Library: altair 6.1.0 | Python 3.14.4
Quality: 88/100 | Updated: 2026-04-24
"""

import os

import altair as alt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: "World's Hardest Sudoku" puzzle (0 = empty)
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

cell_data = []
for row in range(9):
    for col in range(9):
        value = grid[row][col]
        if value != 0:
            cell_data.append({"col": col + 0.5, "row": 8 - row + 0.5, "value": str(value)})

df_numbers = pd.DataFrame(cell_data)

thin_lines = []
thick_lines = []
for i in range(10):
    v_line = {"x": i, "x2": i, "y": 0, "y2": 9}
    h_line = {"x": 0, "x2": 9, "y": i, "y2": i}
    if i % 3 == 0:
        thick_lines.append(v_line)
        thick_lines.append(h_line)
    else:
        thin_lines.append(v_line)
        thin_lines.append(h_line)

df_thin = pd.DataFrame(thin_lines)
df_thick = pd.DataFrame(thick_lines)

# Plot
thin_grid = alt.Chart(df_thin).mark_rule(color=INK_SOFT, strokeWidth=1.2).encode(x="x:Q", x2="x2:Q", y="y:Q", y2="y2:Q")

thick_grid = alt.Chart(df_thick).mark_rule(color=INK, strokeWidth=5).encode(x="x:Q", x2="x2:Q", y="y:Q", y2="y2:Q")

numbers = (
    alt.Chart(df_numbers)
    .mark_text(fontSize=56, fontWeight="bold", color=INK)
    .encode(x="col:Q", y="row:Q", text="value:N")
)

chart = (
    alt.layer(thin_grid, thick_grid, numbers)
    .properties(
        width=900,
        height=900,
        background=PAGE_BG,
        title=alt.Title(
            "sudoku-basic · altair · anyplot.ai",
            fontSize=32,
            fontWeight="normal",
            color=INK,
            anchor="middle",
            offset=24,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(grid=False, domain=False, ticks=False, labels=False, title=None)
    .configure_scale(bandPaddingInner=0, bandPaddingOuter=0)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
