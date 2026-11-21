"""anyplot.ai
line-markers: Line Plot with Markers
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-12
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TIME = "Time (hours)"  # role: x
QUALITY = ["Quality (%)"]  # role: y
BATCH = "Batch"  # role: series

# Data: replace this block with your own table, for example df = pd.read_csv("quality.csv")
rng = np.random.default_rng(42)
times = np.array([1, 3, 6, 9, 12, 15, 18, 22, 26, 30])
batches = {"Batch A": (99.2, 1.5), "Batch B": (98.8, 1.8), "Batch C": (99.5, 1.2)}
df = pd.DataFrame(
    {
        TIME: np.tile(times, len(batches)),
        QUALITY[0]: np.concatenate([mean + rng.normal(0, sd, len(times)) for mean, sd in batches.values()]),
        BATCH: np.repeat(list(batches), len(times)),
    }
)

# Plot
# Marker shapes and line dashes, assigned to the series in order
MARKER_SHAPES = ["circle", "square", "triangle-up", "diamond", "cross", "triangle-down", "stroke", "arrow"]
LINE_DASHES = [[1, 0], [6, 4], [2, 3], [8, 3, 2, 3], [4, 4], [1, 3], [10, 4], [3, 3]]

ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
series = df[BATCH].dropna().drop_duplicates().tolist()

base = alt.Chart(df).encode(
    x=alt.X(TIME.translate(ESCAPE), type="quantitative", title=TIME),
    y=alt.Y(QUALITY[0].translate(ESCAPE), type="quantitative", title=QUALITY[0], scale=alt.Scale(zero=False)),
)
lines = base.mark_line(size=2).encode(
    color=alt.Color(
        BATCH.translate(ESCAPE), type="nominal", legend=None, sort=None, scale=alt.Scale(range=IMPRINT_PALETTE)
    ),
    strokeDash=alt.StrokeDash(
        BATCH.translate(ESCAPE),
        type="nominal",
        sort=None,
        legend=None,
        scale=alt.Scale(domain=series, range=LINE_DASHES[: len(series)]),
    ),
)
points = base.mark_point(filled=True, size=90, opacity=1, strokeWidth=0).encode(
    fill=alt.Fill(
        BATCH.translate(ESCAPE), type="nominal", title=BATCH, sort=None, scale=alt.Scale(range=IMPRINT_PALETTE)
    ),
    shape=alt.Shape(
        BATCH.translate(ESCAPE), type="nominal", title=BATCH, sort=None, scale=alt.Scale(range=MARKER_SHAPES)
    ),
)

chart = (
    (lines + points)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("line-markers · python · altair · anyplot.ai", fontSize=16),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=13,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=12,
        symbolSize=90,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical landscape canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    # Very wide labels can overshoot: scale the whole image down (nothing is cropped)
    fit = min(TARGET_W / img.width, TARGET_H / img.height)
    img = img.resize((int(img.width * fit), int(img.height * fit)), Image.LANCZOS)
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
