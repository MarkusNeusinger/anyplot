""" anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: altair 6.3.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
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

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
YEAR = "Year"  # role: time
SOURCE = "Energy source"  # role: category
SHARE = "Share (%)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("energy.csv")
sources = ["Coal", "Natural Gas", "Nuclear", "Renewables"]
shares = {
    "Coal": [45, 42, 39, 35, 32, 28, 25, 22, 19, 16],
    "Natural Gas": [25, 26, 27, 28, 29, 30, 31, 31, 30, 28],
    "Nuclear": [12, 12.5, 12, 11.5, 12, 12.5, 12, 11, 12.5, 12],
    "Renewables": [18, 19.5, 22, 25.5, 27, 29.5, 32, 36, 36.5, 44],
}
df = pd.DataFrame(
    {
        YEAR: [year for name in sources for year in range(2015, 2025)],
        SOURCE: [name for name in sources for _ in range(10)],
        SHARE: [value for name in sources for value in shares[name]],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
categories = list(df[SOURCE].unique())
df["Stack order"] = df[SOURCE].map({name: i for i, name in enumerate(categories)})

chart = (
    alt.Chart(df)
    .mark_area(opacity=0.85, line=alt.MarkConfig(strokeWidth=1))
    .encode(
        x=alt.X(
            YEAR.translate(ESCAPE),
            type="ordinal",
            title=YEAR,
            axis=alt.Axis(labelAngle=0, labelFontSize=10, titleFontSize=12),
        ),
        y=alt.Y(
            SHARE.translate(ESCAPE),
            type="quantitative",
            title="Share of total (%)",
            stack="normalize",
            axis=alt.Axis(format=".0%", labelFontSize=10, titleFontSize=12),
        ),
        color=alt.Color(
            SOURCE.translate(ESCAPE),
            type="nominal",
            title=SOURCE,
            sort=None,
            scale=alt.Scale(domain=categories, range=IMPRINT_PALETTE[: len(categories)]),
            legend=alt.Legend(
                orient="bottom", direction="horizontal", titleFontSize=11, labelFontSize=10, symbolSize=120
            ),
        ),
        order=alt.Order("Stack order", type="quantitative", sort="ascending"),
        tooltip=[
            alt.Tooltip(YEAR.translate(ESCAPE), type="ordinal", title=YEAR),
            alt.Tooltip(SOURCE.translate(ESCAPE), type="nominal", title=SOURCE),
            alt.Tooltip(SHARE.translate(ESCAPE), type="quantitative", title=SHARE, format=".1f"),
        ],
    )
    .properties(
        width=620,
        height=320,
        title=alt.Title(text="area-stacked-percent · python · altair · anyplot.ai", fontSize=16),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
