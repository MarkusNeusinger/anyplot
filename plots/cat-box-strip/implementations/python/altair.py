""" anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: altair 6.3.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-21
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column names
DEPARTMENT = "Department"  # role: category
QUALITY_SCORE = "Quality Score"  # role: value

# Data: product quality scores across departments
np.random.seed(42)
engineering = np.random.normal(85, 6, 40)  # higher scores, tight distribution
marketing = np.append(np.random.normal(72, 12, 35), [45, 48, 98])  # wider spread plus outliers
sales = np.append(np.random.normal(65, 10, 45), [35, 92, 95])  # lower scores plus outliers
support = np.concatenate([np.random.normal(60, 8, 20), np.random.normal(80, 5, 25)])  # bimodal

groups = {"Engineering": engineering, "Marketing": marketing, "Sales": sales, "Support": support}
df = pd.DataFrame(
    {
        DEPARTMENT: np.repeat(list(groups), [len(v) for v in groups.values()]),
        QUALITY_SCORE: np.clip(np.concatenate(list(groups.values())), 30, 100),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
dept_field = DEPARTMENT.translate(ESCAPE)
score_field = QUALITY_SCORE.translate(ESCAPE)

# Seeded sideways jitter in band units (layout only; values stay on the value axis)
plot_df = df.assign(jitter=np.random.default_rng(7).uniform(-1, 1, len(df)))

x_axis = alt.Axis(labelAngle=0, labelFontSize=11, titleFontSize=12)
y_axis = alt.Axis(labelFontSize=11, titleFontSize=12)
y_scale = alt.Scale(domain=[df[QUALITY_SCORE].min() - 5, df[QUALITY_SCORE].max() + 5], zero=False)

boxplot = (
    alt.Chart(plot_df)
    .mark_boxplot(
        size=70,
        color=IMPRINT_PALETTE[0],
        extent=1.5,
        median={"color": INK, "strokeWidth": 3},
        rule={"color": INK_SOFT},
        box={"fill": IMPRINT_PALETTE[0], "fillOpacity": 0.3, "stroke": IMPRINT_PALETTE[0], "strokeWidth": 1.5},
        outliers=False,
    )
    .encode(
        x=alt.X(dept_field, type="nominal", title=DEPARTMENT, sort=None, axis=x_axis),
        y=alt.Y(score_field, type="quantitative", title=QUALITY_SCORE, scale=y_scale, axis=y_axis),
    )
)

strip = (
    alt.Chart(plot_df)
    .mark_circle(size=22, color=IMPRINT_PALETTE[0], opacity=0.6)
    .encode(
        x=alt.X(dept_field, type="nominal", sort=None),
        xOffset=alt.XOffset("jitter", type="quantitative", scale=alt.Scale(domain=[-2.6, 2.6])),
        y=alt.Y(score_field, type="quantitative"),
        tooltip=[
            alt.Tooltip(dept_field, type="nominal", title=DEPARTMENT),
            alt.Tooltip(score_field, type="quantitative", title=QUALITY_SCORE, format=".1f"),
        ],
    )
)

chart = (
    alt.layer(boxplot, strip)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
        title=alt.Title("cat-box-strip · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_axis(
        gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK, domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}×{h}, exceeds target {TW}×{TH}")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
