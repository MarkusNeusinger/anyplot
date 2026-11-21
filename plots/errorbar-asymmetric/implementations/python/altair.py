"""anyplot.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
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

# Imprint palette: a single series uses position 1 alone
BRAND = "#009E73"

# Columns: set these to your table's column names
PRODUCT = "Product"  # role: x
QUALITY = "Quality score"  # role: y
ERROR_LOWER = "Error below (points)"  # role: error_lower
ERROR_UPPER = "Error above (points)"  # role: error_upper

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
df = pd.DataFrame(
    {
        PRODUCT: ["Product A", "Product B", "Product C", "Product D", "Product E", "Product F"],
        QUALITY: [85.2, 72.8, 91.5, 68.3, 78.9, 82.1],
        ERROR_LOWER: [5.2, 8.1, 3.8, 9.5, 6.3, 4.9],
        ERROR_UPPER: [8.7, 4.3, 6.2, 5.8, 10.1, 7.6],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
LOWER_BOUND = "10th percentile"
UPPER_BOUND = "90th percentile"
bars = df.copy()
bars[LOWER_BOUND] = df[QUALITY] - df[ERROR_LOWER]
bars[UPPER_BOUND] = df[QUALITY] + df[ERROR_UPPER]
y_domain = [float(np.floor(bars[LOWER_BOUND].min() - 4)), float(np.ceil(bars[UPPER_BOUND].max() + 4))]

x_enc = alt.X(
    PRODUCT.translate(ESCAPE),
    type="nominal",
    title=PRODUCT,
    sort=None,
    axis=alt.Axis(labelAngle=0, ticks=False, domain=False),
)
y_scale = alt.Scale(domain=y_domain, zero=False)
low = LOWER_BOUND.translate(ESCAPE)
high = UPPER_BOUND.translate(ESCAPE)

base = alt.Chart(bars)
arms = base.mark_rule(strokeWidth=2.5, color=BRAND).encode(
    x=x_enc,
    y=alt.Y(low, type="quantitative", title=f"{QUALITY} (10th–90th percentile)", scale=y_scale),
    y2=alt.Y2(high),
)
caps = (
    base.transform_fold([low, high], as_=["Bound", "Bound value"])
    .mark_tick(size=26, thickness=2.5, color=BRAND)
    .encode(x=x_enc, y=alt.Y("Bound value:Q", scale=y_scale))
)
points = base.mark_point(size=170, filled=True, color=BRAND, stroke=PAGE_BG, strokeWidth=1.5, opacity=1).encode(
    x=x_enc,
    y=alt.Y(QUALITY.translate(ESCAPE), type="quantitative", scale=y_scale),
    tooltip=[
        alt.Tooltip(PRODUCT.translate(ESCAPE), type="nominal", title=PRODUCT),
        alt.Tooltip(QUALITY.translate(ESCAPE), type="quantitative", title=QUALITY, format=".1f"),
        alt.Tooltip(low, type="quantitative", title=LOWER_BOUND, format=".1f"),
        alt.Tooltip(high, type="quantitative", title=UPPER_BOUND, format=".1f"),
    ],
)

chart = (
    alt.layer(arms, caps, points)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            "errorbar-asymmetric · python · altair · anyplot.ai",
            subtitle="Error bars show the 10th–90th percentile range",
            fontSize=16,
            subtitleFontSize=11,
            subtitleFontStyle="italic",
            anchor="middle",
            color=INK,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        grid=True,
        gridColor=INK,
        gridOpacity=0.12,
        gridWidth=0.5,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
    )
    .configure_axisX(grid=False)
    .configure_view(fill=PAGE_BG, stroke=None)
)

# Save: pad (never crop) the vl-convert output to the 3200 x 1800 target
TARGET_W, TARGET_H = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"vl-convert produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
