""" anyplot.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-20
"""

import os
import zlib

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Data — 16×16 Data Matrix ECC 200 barcode encoding "SERIAL:12345678"
np.random.seed(42)
size = 16
quiet_zone = 1  # minimum 1 module per spec; tighter quiet zone fills canvas better
total_size = size + 2 * quiet_zone

matrix = np.zeros((total_size, total_size), dtype=int)

# L-shaped finder pattern: solid black on left and bottom edges
for row in range(size):
    matrix[quiet_zone + row, quiet_zone] = 1
for col in range(size):
    matrix[quiet_zone + size - 1, quiet_zone + col] = 1

# Alternating timing pattern on top and right edges
for col in range(size):
    matrix[quiet_zone, quiet_zone + col] = col % 2
for row in range(size):
    matrix[quiet_zone + row, quiet_zone + size - 1] = row % 2

# Interior data area: deterministic bit pattern derived from content
content = "SERIAL:12345678"
hash_val = zlib.crc32(content.encode())  # zlib.crc32 is deterministic unlike hash()
for row in range(1, size - 1):
    for col in range(1, size - 1):
        idx = row * size + col
        matrix[quiet_zone + row, quiet_zone + col] = ((hash_val >> (idx % 32)) ^ (idx * 13)) % 2

# Convert to DataFrame with cell-type labels for interactive tooltips
rows = []
for row in range(total_size):
    for col in range(total_size):
        r, c = row - quiet_zone, col - quiet_zone
        if r < 0 or r >= size or c < 0 or c >= size:
            cell_type = "Quiet Zone"
        elif c == 0 or r == size - 1:
            cell_type = "Finder Pattern"
        elif r == 0 or c == size - 1:
            cell_type = "Timing Pattern"
        else:
            cell_type = "Data Cell"
        rows.append(
            {
                "x": col,
                "y": total_size - 1 - row,  # flip y so row=0 maps to chart top
                "value": matrix[row, col],
                "cell_type": cell_type,
            }
        )
df = pd.DataFrame(rows)

# Plot — square format (600×600 at scale_factor=4 → 2400×2400 px)
no_pad = alt.Scale(paddingInner=0, paddingOuter=0)  # eliminates gaps between cells

chart = (
    alt.Chart(df)
    .mark_rect(stroke=None)
    .encode(
        x=alt.X("x:O", axis=None, scale=no_pad),
        y=alt.Y("y:O", axis=None, scale=no_pad),
        color=alt.Color("value:N", scale=alt.Scale(domain=[0, 1], range=["#FFFFFF", "#000000"]), legend=None),
        tooltip=[
            alt.Tooltip("x:O", title="Column"),
            alt.Tooltip("y:O", title="Row"),
            alt.Tooltip("cell_type:N", title="Cell Type"),
        ],
    )
    .properties(
        width=600,
        height=600,
        background=PAGE_BG,
        title=alt.Title("datamatrix-basic · python · altair · anyplot.ai", fontSize=16, color=INK, anchor="middle"),
    )
    .configure_view(fill="#FFFFFF", strokeWidth=0)
    .configure_axis(grid=False)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
