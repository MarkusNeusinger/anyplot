""" anyplot.ai
histogram-overlapping: Overlapping Histograms
Library: altair 6.2.2 | Python 3.13.15
Quality: 88/100 | Updated: 2026-08-18
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (position 1 is ALWAYS #009E73 — see default-style-guide.md)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
DEPARTMENTS = ["Engineering", "Sales", "Support"]
COLOR_SCALE = alt.Scale(domain=DEPARTMENTS, range=IMPRINT_PALETTE[:3])

# Data: support-ticket response times (ms) by department
np.random.seed(42)
engineering = np.random.normal(loc=350, scale=80, size=150)
sales = np.random.normal(loc=420, scale=100, size=150)
support = np.random.normal(loc=280, scale=60, size=150)

df = pd.DataFrame(
    {
        "Response Time (ms)": np.concatenate([engineering, sales, support]),
        "Department": ["Engineering"] * 150 + ["Sales"] * 150 + ["Support"] * 150,
    }
)

# Plot — overlapping semi-transparent histograms; one shared x encoding keeps bin edges aligned
histograms = (
    alt.Chart(df)
    .mark_bar(
        opacity=0.55, binSpacing=0, cornerRadiusTopLeft=2, cornerRadiusTopRight=2, stroke=PAGE_BG, strokeWidth=0.5
    )
    .encode(
        x=alt.X(
            "Response Time (ms):Q",
            bin=alt.Bin(maxbins=24),
            title="Response Time (ms)",
            axis=alt.Axis(labelFontSize=10, titleFontSize=12, grid=False),
        ),
        y=alt.Y(
            "count():Q",
            title="Frequency",
            stack=None,
            axis=alt.Axis(labelFontSize=10, titleFontSize=12, gridColor=INK, gridOpacity=0.15),
        ),
        color=alt.Color(
            "Department:N",
            scale=COLOR_SCALE,
            legend=alt.Legend(
                title="Department",
                titleFontSize=10,
                labelFontSize=10,
                orient="top-right",
                symbolSize=140,
                symbolStrokeWidth=0,
            ),
        ),
        tooltip=[alt.Tooltip("Department:N"), alt.Tooltip("count():Q", title="Count")],
    )
)

# Layer — dashed mean-rule per department, using Altair's inline aggregate encoding shorthand
mean_rules = (
    alt.Chart(df)
    .mark_rule(strokeDash=[6, 4], strokeWidth=2.5, opacity=0.9)
    .encode(x=alt.X("mean(Response Time (ms)):Q"), color=alt.Color("Department:N", scale=COLOR_SCALE, legend=None))
)

title = "histogram-overlapping · python · altair · anyplot.ai"
chart = (
    alt.layer(histograms, mean_rules)
    .properties(
        width=620, height=320, background=PAGE_BG, title=alt.Title(title, fontSize=16, anchor="middle", color=INK)
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(domainColor=INK_SOFT, tickColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save — PNG padded to the canonical 3200×1800 canvas (see prompts/library/altair.md "Canvas")
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TARGET_W, TARGET_H = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TARGET_W or _h > TARGET_H:
    raise SystemExit(
        f"altair vl-convert produced {_w}x{_h}, exceeds target {TARGET_W}x{TARGET_H}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TARGET_W or _h < TARGET_H:
    _canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    _canvas.paste(_img, ((TARGET_W - _w) // 2, (TARGET_H - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
