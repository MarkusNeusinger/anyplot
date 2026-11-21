"""anyplot.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import altair as alt
from altair.datasets import data
from PIL import Image


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential colormap (single polarity): brand green -> blue
IMPRINT_SEQ = ["#009E73", "#4467A3"]
NO_DATA = "#8A8A84"

# Column constants
COUNTY_ID = "id"  # role: join key to the county shapes
RATE = "Unemployment rate"  # role: value shaded on the map

# Data - US unemployment rate by county
counties = alt.topo_feature(data.us_10m.url, "counties")
df = data.unemployment().rename(columns={"rate": RATE})

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
rate_field = RATE.translate(ESCAPE)
title = "US County Unemployment · choropleth-basic · python · altair · anyplot.ai"
title_fontsize = round(18 * min(1.0, 67 / len(title)))

chart = (
    alt.Chart(counties)
    .mark_geoshape(stroke=PAGE_BG, strokeWidth=0.3)
    .encode(
        color=alt.condition(
            f"isValid(datum['{RATE}'])",
            alt.Color(
                rate_field,
                type="quantitative",
                title=RATE,
                scale=alt.Scale(range=IMPRINT_SEQ),
                legend=alt.Legend(format=".0%", gradientLength=200, gradientThickness=14),
            ),
            alt.value(NO_DATA),
        ),
        tooltip=[
            alt.Tooltip(COUNTY_ID, type="nominal", title="County ID"),
            alt.Tooltip(rate_field, type="quantitative", title=RATE, format=".1%"),
        ],
    )
    .transform_lookup(lookup="id", from_=alt.LookupData(df, COUNTY_ID, [RATE]))
    .project(type="albersUsa")
    .properties(width=620, height=320, title=alt.Title(title, fontSize=title_fontsize, anchor="middle"))
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure(background=PAGE_BG)
    .configure_title(color=INK, fontWeight="bold")
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=12,
        orient="right",
        offset=10,
        padding=8,
    )
)

# Save as PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.interactive().save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical landscape canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TARGET_W or h > TARGET_H:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TARGET_W}x{TARGET_H}")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - w) // 2, (TARGET_H - h) // 2))
canvas.save(f"plot-{THEME}.png")
