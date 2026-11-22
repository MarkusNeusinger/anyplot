""" anyplot.ai
chessboard-basic: Chess Board Grid Visualization
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-22
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: classic two-tone board colors, constant across themes
SQUARE_COLORS = {"light": "#F5DEB3", "dark": "#A0704F"}

# Columns: set these to your table's column names
FILE = "File"  # role: columns
RANK = "Rank"  # role: rows
SHADE = "Shade"  # role: extra

# Data: replace this block with your own table of squares, one row per square
# Light squares sit at h1 and a8 (standard orientation)
files = list("abcdefgh")
df = pd.DataFrame(
    [
        {FILE: file, RANK: rank, SHADE: "light" if (i + rank - 1) % 2 == 1 else "dark"}
        for i, file in enumerate(files)
        for rank in range(1, 9)
    ]
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
file_order = list(dict.fromkeys(df[FILE]))
rank_order = sorted(df[RANK].unique(), reverse=True)  # highest rank at the top
shades = list(SQUARE_COLORS)

chart = (
    alt.Chart(df)
    .mark_rect(stroke=INK_SOFT, strokeWidth=1.5)
    .encode(
        x=alt.X(
            FILE.translate(ESCAPE),
            type="ordinal",
            title=None,
            sort=file_order,
            axis=alt.Axis(labelFontSize=24, labelAngle=0, labelPadding=10, labelColor=INK_SOFT, ticks=False),
        ),
        y=alt.Y(
            RANK.translate(ESCAPE),
            type="ordinal",
            title=None,
            sort=rank_order,
            axis=alt.Axis(labelFontSize=24, labelPadding=10, labelColor=INK_SOFT, ticks=False),
        ),
        color=alt.Color(
            SHADE.translate(ESCAPE),
            type="nominal",
            legend=None,
            scale=alt.Scale(domain=shades, range=[SQUARE_COLORS[s] for s in shades]),
        ),
    )
    .properties(
        width=460,
        height=460,
        background=PAGE_BG,
        title=alt.Title(
            "chessboard-basic · python · altair · anyplot.ai", fontSize=24, anchor="middle", offset=20, color=INK
        ),
    )
    .configure_view(strokeWidth=2, stroke=INK_SOFT, fill=PAGE_BG)
    .configure_axis(domainColor=INK_SOFT, grid=False)
)

# Save: pad (never crop) to the 2400 x 2400 square canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TARGET = 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET or img.height > TARGET:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET}x{TARGET}; shrink width/height")
canvas = Image.new("RGB", (TARGET, TARGET), PAGE_BG)
canvas.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
