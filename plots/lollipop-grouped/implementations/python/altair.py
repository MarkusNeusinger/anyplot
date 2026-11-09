""" anyplot.ai
lollipop-grouped: Grouped Lollipop Chart
Library: altair 6.3.0 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
"""

import os

import altair as alt
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
REGION = "Region"  # role: category
QUARTER = "Quarter"  # role: series
SCORE = "Revenue ($M)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
df = pd.DataFrame(
    {
        REGION: ["North"] * 3 + ["South"] * 3 + ["East"] * 3 + ["West"] * 3,
        QUARTER: ["Q1 2024", "Q2 2024", "Q3 2024"] * 4,
        SCORE: [83, 101, 101, 74, 76, 80, 88, 85, 90, 85, 94, 94],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
region_order = df.groupby(REGION, sort=False)[SCORE].sum().sort_values(ascending=False).index.tolist()
quarter_order = df[QUARTER].dropna().unique().tolist()
score_top = df[SCORE].max() * 1.1

title = "lollipop-grouped · python · altair · anyplot.ai"
title_size = round(16 * min(1.0, 67 / len(title)))

base = alt.Chart(df).encode(
    x=alt.X(
        REGION.translate(ESCAPE),
        type="nominal",
        title=f"{REGION} (sorted by total {SCORE.split(' (')[0].lower()})",
        sort=region_order,
        scale=alt.Scale(paddingInner=0.35, paddingOuter=0.2),
        axis=alt.Axis(labelAngle=0),
    ),
    xOffset=alt.XOffset(
        QUARTER.translate(ESCAPE), type="nominal", sort=quarter_order, scale=alt.Scale(paddingOuter=0.6)
    ),
    color=alt.Color(
        QUARTER.translate(ESCAPE),
        type="nominal",
        title=QUARTER,
        sort=quarter_order,
        scale=alt.Scale(range=IMPRINT_PALETTE),
    ),
    tooltip=[
        alt.Tooltip(REGION.translate(ESCAPE), title=REGION),
        alt.Tooltip(QUARTER.translate(ESCAPE), title=QUARTER),
        alt.Tooltip(SCORE.translate(ESCAPE), title=SCORE, format=".0f"),
    ],
)

# Stems: thin rules from the shared zero baseline up to each value
stems = base.mark_rule(strokeWidth=2.5).encode(
    y=alt.Y(
        SCORE.translate(ESCAPE), type="quantitative", title=SCORE, scale=alt.Scale(domain=[0, score_top], nice=False)
    ),
    y2=alt.datum(0),
)

# Markers: circular dots at each value
markers = base.mark_circle(size=220, opacity=1, stroke=PAGE_BG, strokeWidth=1.5).encode(
    y=alt.Y(SCORE.translate(ESCAPE), type="quantitative")
)

chart = (
    (stems + markers)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        padding={"left": 10, "right": 10, "top": 10, "bottom": 10},
        title=alt.Title(title, fontSize=title_size, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0, continuousWidth=620, continuousHeight=320)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
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
    .configure_legend(
        labelFontSize=10,
        titleFontSize=10,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        orient="top",
        direction="horizontal",
        padding=6,
        symbolSize=120,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(
        f"altair vl-convert produced {w}×{h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if w < TW or h < TH:
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
