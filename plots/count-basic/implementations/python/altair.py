""" anyplot.ai
count-basic: Basic Count Plot
Library: altair 6.2.2 | Python 3.13.14
Quality: 92/100 | Updated: 2026-08-11
"""

import os
import sys


sys.path = [p for p in sys.path if not p.endswith("implementations/python")]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Imprint palette position 1

# Data: Survey responses with varying frequencies
np.random.seed(42)
responses = np.random.choice(
    ["Excellent", "Good", "Average", "Poor", "Very Poor"], size=200, p=[0.25, 0.35, 0.20, 0.12, 0.08]
)
df = pd.DataFrame({"Response": responses})

TITLE = "count-basic · python · altair · anyplot.ai"

# Aggregate counts and each category's share of the total via Altair's
# declarative transform pipeline, so the percentage annotation is computed
# inside the chart spec rather than pre-calculated in pandas.
base = (
    alt.Chart(df)
    .transform_aggregate(count="count()", groupby=["Response"])
    .transform_joinaggregate(total="sum(count)")
    .transform_calculate(pct="datum.count / datum.total * 100")
    .transform_calculate(label="format(datum.count, 'd') + ' (' + format(datum.pct, '.0f') + '%)'")
)

# Hover highlight: a real Altair selection, not a decorative effect — fully
# functional in the interactive plot-{THEME}.html export.
hover = alt.selection_point(on="pointerover", fields=["Response"], empty=False)

bars = (
    base.mark_bar(color=BRAND, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X("Response:N", sort="-y", title="Survey Response"),
        y=alt.Y("count:Q", title="Number of Responses"),
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.88)),
        tooltip=[
            alt.Tooltip("Response:N", title="Response"),
            alt.Tooltip("count:Q", title="Count"),
            alt.Tooltip("pct:Q", title="Share", format=".1f"),
        ],
    )
    .add_params(hover)
)

labels = base.mark_text(align="center", baseline="bottom", dy=-6, fontSize=13, fontWeight="bold", color=INK).encode(
    x=alt.X("Response:N", sort="-y"), y="count:Q", text="label:N"
)

chart = (
    (bars + labels)
    .properties(
        width=620,  # inner-view landscape target — see prompts/library/altair.md "Canvas"
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            TITLE,
            subtitle=f"n = {len(df)} survey responses",
            fontSize=16,
            color=INK,
            subtitleFontSize=12,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)  # no boxed frame — L-shaped spines via axis domain lines only
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.12,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Canvas contract: pad the rendered PNG up to the exact target — never crop,
# since cropping would clip the title/axis labels (see prompts/library/altair.md).
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TARGET_W or h > TARGET_H:
    raise SystemExit(
        f"altair vl-convert produced {w}x{h}, exceeds target {TARGET_W}x{TARGET_H}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if w < TARGET_W or h < TARGET_H:
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - w) // 2, (TARGET_H - h) // 2))
    canvas.save(f"plot-{THEME}.png")
