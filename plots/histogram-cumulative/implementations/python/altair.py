"""anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-11
"""

import os
import sys


# The script is named altair.py: drop its own directory from sys.path so the real package imports
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.dirname(os.path.abspath(__file__))]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, first series is brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 30  # number of histogram bins
TARGET_W, TARGET_H = 3200, 1800  # canonical landscape canvas

# Columns: set these to your table's column names
USAGE = "Electricity Usage (kWh)"  # role: numeric
CUM_PROPORTION = "Cumulative Proportion"  # role: extra
CUM_COUNT = "Cumulative Count"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("usage.csv")
np.random.seed(42)
df = pd.DataFrame({USAGE: np.concatenate([np.random.normal(250, 50, 300), np.random.normal(450, 80, 200)])})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
values = df[USAGE].dropna().to_numpy()
bin_edges = np.linspace(values.min() - 10, values.max() + 10, N_BINS + 1)
counts, edges = np.histogram(values, bins=bin_edges)
cumulative_counts = np.cumsum(counts)
steps = pd.DataFrame(
    {USAGE: edges[:-1], CUM_PROPORTION: cumulative_counts / cumulative_counts[-1], CUM_COUNT: cumulative_counts}
)

chart = (
    alt.Chart(steps)
    .mark_area(
        interpolate="step-after",
        color=IMPRINT_PALETTE[0],
        opacity=0.8,
        line={"color": IMPRINT_PALETTE[0], "strokeWidth": 2},
    )
    .encode(
        x=alt.X(
            USAGE.translate(ESCAPE),
            type="quantitative",
            title=USAGE,
            scale=alt.Scale(domain=[float(bin_edges[0]), float(bin_edges[-1])]),
        ),
        y=alt.Y(
            CUM_PROPORTION.translate(ESCAPE), type="quantitative", title=CUM_PROPORTION, scale=alt.Scale(domain=[0, 1])
        ),
        tooltip=[
            alt.Tooltip(USAGE.translate(ESCAPE), type="quantitative", title="Usage (kWh)", format=".1f"),
            alt.Tooltip(CUM_PROPORTION.translate(ESCAPE), type="quantitative", title="Cumulative %", format=".1%"),
            alt.Tooltip(CUM_COUNT.translate(ESCAPE), type="quantitative", title="Count"),
        ],
    )
    .properties(
        width=620,
        height=320,
        padding={"left": 5, "right": 10, "top": 5, "bottom": 10},
        background=PAGE_BG,
        title=alt.Title("histogram-cumulative · python · altair · anyplot.ai", fontSize=16),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, continuousWidth=620, continuousHeight=320)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK_SOFT,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=10,
        titleColor=INK,
        titleFontSize=12,
    )
    .configure_title(color=INK, fontSize=16)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save PNG, then pad (never crop) to the exact canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")

# Save interactive HTML
chart.save(f"plot-{THEME}.html")
