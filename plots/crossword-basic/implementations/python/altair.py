"""anyplot.ai
crossword-basic: Crossword Puzzle Grid
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
"""

import os
import sys


# Prevent the script's own directory from shadowing the 'altair' package
sys.path = [p for p in sys.path if not p.endswith("/python")]

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Crossword cell colors (theme-adaptive monochrome design)
CELL_ENTRY = "#FFFFFF" if THEME == "light" else "#DEDAD3"
CELL_BLOCK = "#1A1A17" if THEME == "light" else "#3E3E3A"
NUMBER_INK = "#1A1A17" if THEME == "light" else "#2A2A26"  # on the entry cells

# Columns: set these to your table's column names
ROW = "Row"  # role: extra
COL = "Column"  # role: extra
GRID = "Blocked"  # role: grid

# Data: replace this block with your own table, for example df = pd.read_csv("grid.csv")
# One row per cell; Blocked is 1 for a blocking cell and 0 for an entry cell.
# 15x15 crossword grid with 180-degree rotational symmetry.
black_positions = [
    (0, 4), (0, 10), (1, 4), (1, 10), (2, 7), (3, 0), (3, 6), (3, 11), (3, 12), (4, 3), (4, 8),
    (4, 13), (4, 14), (5, 5), (5, 9), (6, 2), (6, 7), (6, 12), (7, 2), (7, 7), (7, 12),
]  # fmt: skip
size = 15
blocked = {(r, c) for r, c in black_positions} | {(size - 1 - r, size - 1 - c) for r, c in black_positions}
df = pd.DataFrame(
    {
        ROW: [r for r in range(size) for c in range(size)],
        COL: [c for r in range(size) for c in range(size)],
        GRID: [int((r, c) in blocked) for r in range(size) for c in range(size)],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
n_rows = int(df[ROW].max()) + 1
n_cols = int(df[COL].max()) + 1
grid = df.pivot(index=ROW, columns=COL, values=GRID).to_numpy()

# Number every entry cell that starts an across or a down word
numbers = []
for r in range(n_rows):
    for c in range(n_cols):
        if grid[r, c] == 1:
            continue
        starts_across = (c == 0 or grid[r, c - 1] == 1) and (c < n_cols - 1 and grid[r, c + 1] == 0)
        starts_down = (r == 0 or grid[r - 1, c] == 1) and (r < n_rows - 1 and grid[r + 1, c] == 0)
        if starts_across or starts_down:
            numbers.append({ROW: r, COL: c, "Number": str(len(numbers) + 1)})
numbers_df = pd.DataFrame(numbers)

CELL_COLOR = "Cell color"
cells_df = df.copy()
cells_df[CELL_COLOR] = np.where(df[GRID] == 1, CELL_BLOCK, CELL_ENTRY)

# Grid cells layer
cells = (
    alt.Chart(cells_df)
    .mark_rect(stroke=INK_SOFT, strokeWidth=1.5)
    .encode(
        x=alt.X(COL.translate(ESCAPE), type="ordinal", axis=None),
        y=alt.Y(ROW.translate(ESCAPE), type="ordinal", axis=None),
        color=alt.Color(CELL_COLOR.translate(ESCAPE), type="nominal", scale=None),
    )
)

# Clue numbers overlay (dark ink: the entry cells are light in both themes)
clue_numbers = (
    alt.Chart(numbers_df)
    .mark_text(align="left", baseline="top", dx=-12, dy=-12, fontSize=10, fontWeight="bold", color=NUMBER_INK)
    .encode(
        x=alt.X(COL.translate(ESCAPE), type="ordinal", axis=None),
        y=alt.Y(ROW.translate(ESCAPE), type="ordinal", axis=None),
        text=alt.Text("Number", type="nominal"),
    )
)

# Compose chart — square 540×540 view → 2400×2400 px at scale=4
chart = (
    (cells + clue_numbers)
    .properties(
        width=540,
        height=540,
        background=PAGE_BG,
        title=alt.Title(
            "crossword-basic · python · altair · anyplot.ai", fontSize=16, anchor="middle", offset=18, color=INK
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad (never crop) to the 2400 x 2400 target
TARGET = 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET or img.height > TARGET:
    raise SystemExit(f"vl-convert produced {img.width}x{img.height}, exceeds {TARGET}x{TARGET}")
canvas = Image.new("RGB", (TARGET, TARGET), PAGE_BG)
canvas.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
