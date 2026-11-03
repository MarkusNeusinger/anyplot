"""anyplot.ai
funnel-basic: Basic Funnel Chart
Library: altair 6.1.0 | Python 3.14.4
Quality: pending | Updated: 2026-04-26
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per stage in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
STAGE = "Stage"  # role: stage
VALUE = "Count"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("funnel.csv")
df = pd.DataFrame(
    {STAGE: ["Awareness", "Interest", "Consideration", "Intent", "Purchase"], VALUE: [1000, 600, 400, 200, 100]}
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
stage_field = STAGE.translate(ESCAPE)
value_field = VALUE.translate(ESCAPE)

funnel = df.copy()
funnel["percentage"] = (funnel[VALUE] / funnel[VALUE].iloc[0] * 100).round(1)
funnel["label"] = funnel[VALUE].astype(str) + "  ·  " + funnel["percentage"].astype(str) + "%"

# Centered funnel: bars span [-value/2, +value/2]
funnel["x_start"] = -funnel[VALUE] / 2
funnel["x_end"] = funnel[VALUE] / 2

half_span = funnel[VALUE].max() / 2 * 1.24
x_scale = alt.Scale(domain=[-half_span, half_span])
row_step = 320 / len(funnel)

# Funnel bars (centered, narrowing)
bars = (
    alt.Chart(funnel)
    .mark_bar(cornerRadius=3, height=row_step * 0.86, stroke=PAGE_BG, strokeWidth=1)
    .encode(
        x=alt.X("x_start", type="quantitative", axis=None, scale=x_scale),
        x2="x_end",
        y=alt.Y(
            stage_field,
            type="nominal",
            title=None,
            sort=None,
            axis=alt.Axis(labelPadding=10, ticks=False, domain=False),
        ),
        color=alt.Color(stage_field, type="nominal", sort=None, scale=alt.Scale(range=IMPRINT_PALETTE), legend=None),
        tooltip=[
            alt.Tooltip(stage_field, type="nominal", title=STAGE),
            alt.Tooltip(value_field, type="quantitative", title=VALUE, format=","),
            alt.Tooltip("percentage", type="quantitative", title="% of top", format=".1f"),
        ],
    )
)

# Value + percentage labels positioned to the right of each bar
labels = (
    alt.Chart(funnel)
    .mark_text(align="left", baseline="middle", dx=8, fontSize=11, fontWeight="bold", color=INK)
    .encode(
        x=alt.X("x_end", type="quantitative", scale=x_scale, axis=None),
        y=alt.Y(stage_field, type="nominal", sort=None),
        text="label",
    )
)

chart = (
    (bars + labels)
    .properties(
        width=620,
        height=320,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
        background=PAGE_BG,
        title=alt.Title(
            "Sales Funnel · funnel-basic · python · altair · anyplot.ai",
            fontSize=16,
            color=INK,
            anchor="middle",
            offset=12,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None, continuousWidth=620, continuousHeight=320)
    .configure_axis(
        labelFontSize=11,
        labelFontWeight="bold",
        labelColor=INK,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        grid=False,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad (never crop) to the canonical landscape canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TARGET_W or h > TARGET_H:
    raise SystemExit(f"altair vl-convert produced {w}×{h}, exceeds target {TARGET_W}×{TARGET_H}")
if (w, h) != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - w) // 2, (TARGET_H - h) // 2))
    canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
