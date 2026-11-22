"""anyplot.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
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

# Imprint palette: all eight positions, one per component in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: category
PRODUCT = "Product"  # role: component
REVENUE = "Revenue ($K)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
df = pd.DataFrame(
    {
        QUARTER: ["Q1", "Q1", "Q1", "Q2", "Q2", "Q2", "Q3", "Q3", "Q3", "Q4", "Q4", "Q4"],
        PRODUCT: ["Software", "Hardware", "Services"] * 4,
        REVENUE: [120, 85, 45, 145, 92, 58, 165, 88, 72, 185, 95, 80],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
quarter, product, revenue = (c.translate(ESCAPE) for c in (QUARTER, PRODUCT, REVENUE))
components = list(dict.fromkeys(df[PRODUCT]))

totals = df.groupby(QUARTER, sort=False, as_index=False)[REVENUE].sum()
totals["label"] = totals[REVENUE].map(lambda v: f"${v:,.0f}K")
y_scale = alt.Scale(domain=[0, totals[REVENUE].max() * 1.12], nice=False)

bars = (
    alt.Chart(df)
    .mark_bar(stroke=PAGE_BG, strokeWidth=0.8, size=90)
    .encode(
        x=alt.X(quarter, type="nominal", title=QUARTER, sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(revenue, type="quantitative", title=REVENUE, scale=y_scale),
        color=alt.Color(
            product, type="nominal", title=PRODUCT, sort=None, scale=alt.Scale(domain=components, range=IMPRINT_PALETTE)
        ),
        order=alt.Order("component_order:Q"),
        tooltip=[
            alt.Tooltip(quarter, title=QUARTER),
            alt.Tooltip(product, title=PRODUCT),
            alt.Tooltip(revenue, title=REVENUE),
        ],
    )
    .transform_calculate(component_order=f"indexof({components}, datum[{PRODUCT!r}])")
)

labels = (
    alt.Chart(totals)
    .mark_text(fontSize=13, fontWeight="bold", dy=-9, color=INK, align="center")
    .encode(x=alt.X(quarter, type="nominal", sort=None), y=alt.Y(revenue, type="quantitative"), text="label:N")
)

chart = (
    (bars + labels)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("bar-stacked-labeled · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0.5)
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
        symbolSize=140,
        labelLimit=110,
        titleLimit=110,
        padding=6,
    )
)

# Save outputs, narrowing the view when long labels push the PNG past the canvas
SCALE = 4
TARGET_W, TARGET_H = 3200, 1800
view_w, view_h = 620, 320
for _ in range(4):
    chart.properties(width=view_w, height=view_h).save(f"plot-{THEME}.png", scale_factor=SCALE)
    img = Image.open(f"plot-{THEME}.png").convert("RGB")
    over_w, over_h = img.width - TARGET_W, img.height - TARGET_H
    if over_w <= 0 and over_h <= 0:
        break
    view_w -= max(over_w, 0) // SCALE + 1
    view_h -= max(over_h, 0) // SCALE + 1
chart.properties(width=view_w, height=view_h).save(f"plot-{THEME}.html")

# Pad (never crop) to the exact canvas
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
