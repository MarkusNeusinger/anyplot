"""anyplot.ai
bar-error: Bar Chart with Error Bars
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
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

# Imprint palette: first position is the single series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TREATMENT = "Treatment group"  # role: category
RESPONSE = "Response rate (%)"  # role: value
ERROR = "Standard deviation (%)"  # role: error

# Data: replace this block with your own table, for example df = pd.read_csv("treatments.csv")
df = pd.DataFrame(
    {
        TREATMENT: ["Control", "Drug A", "Drug B", "Drug C", "Combination"],
        RESPONSE: [45.2, 62.8, 58.3, 71.5, 82.1],
        ERROR: [8.5, 12.3, 9.8, 15.2, 11.7],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
LOWER = "Lower bound"
UPPER = "Upper bound"
df[LOWER] = df[RESPONSE] - df[ERROR]
df[UPPER] = df[RESPONSE] + df[ERROR]

WIDTH, HEIGHT = 620, 320
x_enc = alt.X(
    TREATMENT.translate(ESCAPE),
    type="nominal",
    title=TREATMENT,
    sort=None,
    axis=alt.Axis(labelAngle=0, labelFontSize=12, titleFontSize=14, labelPadding=6, titlePadding=10),
)
y_top = max(100, df[UPPER].max() * 1.05)

base = alt.Chart(df)

bars = base.mark_bar(size=56, color=IMPRINT_PALETTE[0]).encode(
    x=x_enc,
    y=alt.Y(
        RESPONSE.translate(ESCAPE),
        type="quantitative",
        title=RESPONSE,
        scale=alt.Scale(domain=[0, y_top]),
        axis=alt.Axis(labelFontSize=12, titleFontSize=14, titlePadding=10),
    ),
    tooltip=[
        alt.Tooltip(TREATMENT.translate(ESCAPE), type="nominal", title=TREATMENT),
        alt.Tooltip(RESPONSE.translate(ESCAPE), type="quantitative", title=RESPONSE, format=".1f"),
        alt.Tooltip(ERROR.translate(ESCAPE), type="quantitative", title=ERROR, format=".1f"),
    ],
)

error_stem = base.mark_rule(strokeWidth=1.6, color=INK).encode(
    x=x_enc, y=alt.Y(LOWER, type="quantitative"), y2=alt.Y2(UPPER)
)

caps = (
    base.mark_tick(size=22, thickness=1.6, color=INK)
    .transform_fold([LOWER, UPPER], as_=["end", "bound"])
    .encode(x=x_enc, y=alt.Y("bound:Q"))
)

note = (
    alt.Chart(pd.DataFrame({"text": ["Error bars: ±1 SD"]}))
    .mark_text(align="left", baseline="top", fontSize=12, color=INK_SOFT)
    .encode(x=alt.value(10), y=alt.value(8), text="text:N")
)

chart = (
    alt.layer(bars, error_stem, caps, note)
    .properties(
        width=WIDTH,
        height=HEIGHT,
        background=PAGE_BG,
        title=alt.Title("bar-error · python · altair · anyplot.ai", fontSize=18, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save: PNG padded (never cropped) to the 3200 x 1800 target, plus interactive HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair rendered {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}; shrink width/height")
if img.size != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
