""" anyplot.ai
histogram-stepwise: Step Histogram
Library: altair 6.3.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 25  # number of equal-width bins

# Columns: set these to your table's column names
VALUES = ["Measurement Value"]  # role: values
VALUE = VALUES[0]
COUNT = "Frequency"  # computed below: observations per bin

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
np.random.seed(42)
df = pd.DataFrame({VALUE: np.concatenate([np.random.normal(25, 5, 300), np.random.normal(45, 8, 200)])})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
counts, bin_edges = np.histogram(df[VALUE].dropna(), bins=N_BINS)

# Step outline: each bin contributes a horizontal segment at its count; the line starts and ends on the baseline
steps = pd.DataFrame(
    {
        VALUE: np.concatenate([[bin_edges[0]], np.repeat(bin_edges, 2)[1:-1], [bin_edges[-1]]]),
        COUNT: np.concatenate([[0], np.repeat(counts, 2), [0]]),
    }
)
steps["order"] = np.arange(len(steps))

chart = (
    alt.Chart(steps)
    .mark_line(strokeWidth=3, color=IMPRINT_PALETTE[0], interpolate="linear")
    .encode(
        x=alt.X(VALUE.translate(ESCAPE), type="quantitative", title=VALUE),
        y=alt.Y(
            COUNT.translate(ESCAPE),
            type="quantitative",
            title=COUNT,
            scale=alt.Scale(domain=[0, steps[COUNT].max() * 1.05]),
        ),
        order=alt.Order("order:Q"),
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("histogram-stepwise · python · altair · anyplot.ai", fontSize=16),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        domainOpacity=1,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.1,
        labelColor=INK_SOFT,
        labelFontSize=10,
        titleColor=INK,
        titleFontSize=12,
        labelPadding=6,
        titlePadding=8,
    )
    .configure_axisBottom(domainWidth=1)
    .configure_axisLeft(domainWidth=1)
    .configure_title(color=INK, anchor="start", offset=10)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

# Save: render at 4x, then pad (never crop) to the 3200 x 1800 target
TARGET_W, TARGET_H = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TARGET_W or h > TARGET_H:
    raise SystemExit(f"vl-convert produced {w}x{h}, exceeds target {TARGET_W}x{TARGET_H}; shrink width/height")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - w) // 2, (TARGET_H - h) // 2))
canvas.save(f"plot-{THEME}.png")
