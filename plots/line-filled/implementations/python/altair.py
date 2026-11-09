""" anyplot.ai
line-filled: Filled Line Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-09
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — a single-series plot uses it alone

# Columns: set these to your table's column names
DAY = "Day of month"  # role: x
VISITORS = "Daily visitors"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
np.random.seed(42)
days = np.arange(1, 31)
base = 5000 + days * 100  # growth trend
weekly_pattern = 800 * np.sin(2 * np.pi * days / 7)  # weekly cycle
noise = np.random.normal(0, 300, len(days))
df = pd.DataFrame({DAY: days, VISITORS: np.maximum(base + weekly_pattern + noise, 1000)})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
title = "line-filled · python · altair · anyplot.ai"
title_size = round(16 * (67 / len(title) if len(title) > 67 else 1.0))

chart = (
    alt.Chart(df)
    .mark_area(
        line={"color": BRAND, "strokeWidth": 2.5},
        interpolate="linear",
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color="rgba(0, 158, 115, 0.45)", offset=0),
                alt.GradientStop(color="rgba(0, 158, 115, 0.12)", offset=1),
            ],
            x1=1,
            x2=1,
            y1=0,
            y2=1,
        ),
    )
    .encode(
        x=alt.X(DAY.translate(ESCAPE), type="quantitative", title=DAY, scale=alt.Scale(nice=False)),
        y=alt.Y(VISITORS.translate(ESCAPE), type="quantitative", title=VISITORS, scale=alt.Scale(zero=True)),
        tooltip=[
            alt.Tooltip(DAY.translate(ESCAPE), title=DAY),
            alt.Tooltip(VISITORS.translate(ESCAPE), title=VISITORS, format=",.0f"),
        ],
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        padding={"left": 16, "right": 24, "top": 12, "bottom": 12},
        title=alt.Title(title, fontSize=title_size, fontWeight="normal", anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0, continuousWidth=620, continuousHeight=320)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        titleFontWeight="normal",
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        ticks=False,
        labelColor=INK_SOFT,
        titleColor=INK,
        gridColor=INK,
        gridOpacity=0.12,
    )
    .configure_axisX(grid=False)
    .configure_title(color=INK)
    .interactive()
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(
        f"altair vl-convert produced {w}×{h}, exceeds target {TW}×{TH}. "
        "Shrink chart .properties(width=, height=) values and re-render."
    )
if w < TW or h < TH:
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
