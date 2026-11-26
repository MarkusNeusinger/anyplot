""" anyplot.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-26
"""

import os
import sys


# Remove this file's directory from sys.path to avoid circular import with the altair package
if sys.path and os.path.exists(os.path.join(sys.path[0] or ".", "altair.py")):
    sys.path = sys.path[1:]

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Constants: a Data Matrix is black modules on a white tile in both themes
MODULE_ON = "#000000"
MODULE_OFF = "#FFFFFF"

# Columns
COLUMN = "Column"  # role: extra
ROW = "Row"  # role: extra
MODULE = "Module"  # role: extra

# Data: 16×16 ECC 200 symbol for the content, one row per module (1 = black), quiet zone included.
# Replace CONTENT (and SIZE) or load your own module grid into df.
CONTENT = "SERIAL:12345678"
SIZE = 16  # modules per side, without the quiet zone
QUIET_ZONE = 1  # modules of blank margin on every side

grid = np.zeros((SIZE, SIZE), dtype=int)
grid[:, 0] = 1  # finder: solid left edge
grid[-1, :] = 1  # finder: solid bottom edge
grid[0, :] = (np.arange(SIZE) % 2 == 0).astype(int)  # clock: alternating top edge
grid[:, -1] = (np.arange(SIZE) % 2 == 1).astype(int)  # clock: alternating right edge, black in the corner
grid[0, 0] = 1
grid[-1, -1] = 1
# Data modules: deterministic bits seeded from the content
rng = np.random.default_rng(list(CONTENT.encode()))
grid[1:-1, 1:-1] = rng.integers(0, 2, size=(SIZE - 2, SIZE - 2))

symbol = np.pad(grid, QUIET_ZONE, constant_values=0)
rows, cols = np.indices(symbol.shape)
df = pd.DataFrame({COLUMN: cols.ravel(), ROW: rows.ravel(), MODULE: symbol.ravel()})

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
title = "datamatrix-basic · python · altair · anyplot.ai"
no_pad = alt.Scale(paddingInner=0, paddingOuter=0)  # modules touch: no sub-pixel gaps

# Square canvas; the title takes TITLE_BAND px of height, so the side padding is widened by the
# same amount to keep the view (the symbol tile) square.
TITLE_BAND = 36
side = 10 + TITLE_BAND // 2

chart = (
    alt.Chart(df)
    .mark_rect(stroke=None)
    .encode(
        x=alt.X(COLUMN.translate(ESCAPE), type="ordinal", axis=None, scale=no_pad),
        y=alt.Y(ROW.translate(ESCAPE), type="ordinal", axis=None, scale=no_pad),
        color=alt.Color(
            MODULE.translate(ESCAPE),
            type="nominal",
            legend=None,
            scale=alt.Scale(domain=[1, 0], range=[MODULE_ON, MODULE_OFF]),
        ),
    )
    .properties(
        width=600,
        height=600,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding={"left": side, "right": side, "top": 10, "bottom": 10},
        background=PAGE_BG,
        title=alt.Title(
            title,
            subtitle=f"Content: {CONTENT}  ·  {SIZE}×{SIZE} ECC 200  ·  {QUIET_ZONE}-module quiet zone",
            fontSize=16,
            subtitleFontSize=12,
            color=INK,
            subtitleColor=INK_SOFT,
            anchor="middle",
        ),
    )
    .configure_view(fill=MODULE_OFF, strokeWidth=0)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
