""" anyplot.ai
line-stepwise: Step Line Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
"""

import os
import sys


# Workaround for import conflict: remove script directory from path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is always brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DAY = "Day"  # role: x
PRICE = "Price ($)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
price_changes = [0, 0, 5, 5, 0, -3, -3, -3, 8, 8, 8, 2, 2, -2, -2, -2, 6, 6, 3, 3, 3, 1, 1, 1, 0]
df = pd.DataFrame({DAY: np.arange(len(price_changes)), PRICE: 100 + np.cumsum(price_changes)})

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
chart = (
    alt.Chart(df)
    .mark_line(interpolate="step-after", strokeWidth=3, color=IMPRINT_PALETTE[0])
    .encode(
        x=alt.X(DAY.translate(ESCAPE), type="quantitative", title=DAY),
        y=alt.Y(PRICE.translate(ESCAPE), type="quantitative", title=PRICE, scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip(DAY.translate(ESCAPE), title=DAY), alt.Tooltip(PRICE.translate(ESCAPE), title=PRICE)],
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("line-stepwise · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.15,
        gridDash=[4, 4],
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK)
)

# Save: PNG padded (never cropped) to the 3200 x 1800 landscape target, plus interactive HTML
TW, TH = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}×{h}, exceeds target {TW}×{TH}. Shrink width/height.")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
