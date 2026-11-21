""" anyplot.ai
facet-grid: Faceted Grid Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
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

# Imprint palette: all eight positions, one per crop in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
WATER = "Water Usage (mm)"  # role: x
YIELD = "Yield (tons/ha)"  # role: y
SOIL = "Soil Type"  # role: row_facet
SEASON = "Season"  # role: col_facet
CROP = "Crop"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("crops.csv")
np.random.seed(42)
rows = []
for soil in ["Sandy", "Clay", "Loam"]:
    for season in ["Spring", "Summer", "Fall"]:
        for crop in ["Wheat", "Corn", "Soybean"]:
            base_yield = {"Sandy": 3.5, "Clay": 4.0, "Loam": 5.0}[soil]
            season_mult = {"Spring": 0.9, "Summer": 1.1, "Fall": 1.0}[season]
            crop_base = {"Wheat": 3.8, "Corn": 4.5, "Soybean": 3.2}[crop]
            yield_val = np.random.normal(base_yield * season_mult + crop_base, 0.8, 20)
            water = np.random.normal(50 + crop_base * 5, 8, 20)
            for y, w in zip(yield_val, water, strict=True):
                rows.append({WATER: max(20, w), YIELD: max(0.5, y), SOIL: soil, SEASON: season, CROP: crop})
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
TW, TH = 3200, 1800
header = {"titleFontSize": 12, "labelFontSize": 11, "titleColor": INK, "labelColor": INK}

chart = (
    alt.Chart(df)
    .mark_circle(size=28, opacity=0.7)
    .encode(
        x=alt.X(WATER.translate(ESCAPE), type="quantitative", title=WATER, scale=alt.Scale(zero=False)),
        y=alt.Y(YIELD.translate(ESCAPE), type="quantitative", title=YIELD, scale=alt.Scale(zero=False)),
        color=alt.Color(
            CROP.translate(ESCAPE), type="nominal", title=CROP, sort=None, scale=alt.Scale(range=IMPRINT_PALETTE)
        ),
        tooltip=[alt.Tooltip(c.translate(ESCAPE), title=c) for c in [WATER, YIELD, SOIL, SEASON, CROP]],
    )
    .properties(width=570 // df[SEASON].nunique(), height=276 // df[SOIL].nunique())
    .facet(
        column=alt.Column(
            SEASON.translate(ESCAPE),
            type="ordinal",
            title=SEASON,
            sort=list(df[SEASON].unique()),
            header=alt.Header(**header),
        ),
        row=alt.Row(
            SOIL.translate(ESCAPE),
            type="ordinal",
            title=SOIL,
            sort=list(df[SOIL].unique()),
            header=alt.Header(**header),
        ),
    )
    .configure_axis(
        labelFontSize=9,
        titleFontSize=11,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_legend(
        titleFontSize=11,
        labelFontSize=10,
        symbolSize=70,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        padding=6,
    )
    .configure_title(fontSize=14, color=INK)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .properties(title="facet-grid · python · altair · anyplot.ai", background=PAGE_BG)
)

# Save as PNG and HTML, padding the PNG to the exact canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
fit = min(1.0, TW / img.width, TH / img.height)  # shrink only when the grid overshoots; never crop
img = img.resize((int(img.width * fit), int(img.height * fit)), Image.LANCZOS)
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
