""" anyplot.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: altair 6.3.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-20
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

# Imprint palette: first position is the single-series color
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MAX_BINS = 25  # histogram bins for both marginals

# Columns: set these to your table's column names
X_VALUE = "X value (units)"  # role: x
Y_VALUE = "Y value (units)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
rng = np.random.default_rng(42)
n = 150
x = rng.normal(50, 15, n)
y = 0.7 * x + rng.normal(0, 10, n) + 20
df = pd.DataFrame({X_VALUE: x, Y_VALUE: y})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
x_field = X_VALUE.translate(ESCAPE)
y_field = Y_VALUE.translate(ESCAPE)

# Shared domains keep the marginals aligned with the scatter axes
x_domain = [df[X_VALUE].min() - 2, df[X_VALUE].max() + 2]
y_domain = [df[Y_VALUE].min() - 2, df[Y_VALUE].max() + 2]

MAIN_W, MAIN_H, MARGINAL = 560, 300, 60
no_axis = alt.Axis(labels=False, ticks=False, title=None, grid=False)

scatter = (
    alt.Chart(df)
    .mark_circle(size=50, opacity=0.65, color=IMPRINT_PALETTE[0])
    .encode(
        x=alt.X(x_field, type="quantitative", title=X_VALUE, scale=alt.Scale(domain=x_domain)),
        y=alt.Y(y_field, type="quantitative", title=Y_VALUE, scale=alt.Scale(domain=y_domain)),
        tooltip=[
            alt.Tooltip(x_field, type="quantitative", title=X_VALUE),
            alt.Tooltip(y_field, type="quantitative", title=Y_VALUE),
        ],
    )
    .properties(width=MAIN_W, height=MAIN_H)
)

top_hist = (
    alt.Chart(df)
    .mark_bar(color=IMPRINT_PALETTE[0], opacity=0.5)
    .encode(
        x=alt.X(
            x_field, type="quantitative", bin=alt.Bin(maxbins=MAX_BINS), axis=no_axis, scale=alt.Scale(domain=x_domain)
        ),
        y=alt.Y("count()", axis=no_axis),
    )
    .properties(width=MAIN_W, height=MARGINAL)
)

right_hist = (
    alt.Chart(df)
    .mark_bar(color=IMPRINT_PALETTE[0], opacity=0.5)
    .encode(
        y=alt.Y(
            y_field, type="quantitative", bin=alt.Bin(maxbins=MAX_BINS), axis=no_axis, scale=alt.Scale(domain=y_domain)
        ),
        x=alt.X("count()", axis=no_axis),
    )
    .properties(width=MARGINAL, height=MAIN_H)
)

chart = (
    alt.vconcat(top_hist, alt.hconcat(scatter, right_hist, spacing=4), spacing=4)
    .properties(
        background=PAGE_BG,
        title=alt.Title(
            text="scatter-marginal · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK
        ),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=10,
        titleColor=INK,
        titleFontSize=12,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0.5)
)

# Save outputs, padding (never cropping) to the 3200 x 1800 target
TARGET_W, TARGET_H = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}; shrink the view sizes")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
