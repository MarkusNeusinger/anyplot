""" anyplot.ai
point-basic: Point Estimate Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os
from pathlib import Path

import altair as alt
import pandas as pd
from PIL import Image


# Save next to this script so the render lands in the implementation folder
os.chdir(Path(__file__).parent)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the single series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
REFERENCE_COLOR = "#888888"

# Constants
NULL_VALUE = 0  # the no-effect value the reference line marks

# Columns: set these to your table's column names
GROUP = "Group"  # role: category
ESTIMATE = "Effect size"  # role: estimate
LOWER = "Lower 95% CI"  # role: lower_bound
UPPER = "Upper 95% CI"  # role: upper_bound

# Data: replace this block with your own table, for example df = pd.read_csv("effects.csv")
estimates = [2.4, 1.8, 3.1, -0.5, 0.2, 0.8]
half_widths = [0.8, 1.2, 0.6, 1.0, 0.9, 1.1]
df = pd.DataFrame(
    {
        GROUP: ["Treatment A", "Treatment B", "Treatment C", "Treatment D", "Control", "Placebo"],
        ESTIMATE: estimates,
        LOWER: [e - w for e, w in zip(estimates, half_widths, strict=True)],
        UPPER: [e + w for e, w in zip(estimates, half_widths, strict=True)],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
group_f, est_f, low_f, up_f = (c.translate(ESCAPE) for c in (GROUP, ESTIMATE, LOWER, UPPER))

lo, hi = df[LOWER].min(), df[UPPER].max()
pad = (hi - lo) * 0.08
x_scale = alt.Scale(domain=[min(lo - pad, NULL_VALUE - pad), max(hi + pad, NULL_VALUE + pad)])


def y_enc():
    return alt.Y(group_f, type="nominal", title=None, sort=None)


points = (
    alt.Chart(df)
    .mark_point(size=260, filled=True, color=BRAND, opacity=1)
    .encode(
        x=alt.X(est_f, type="quantitative", title=ESTIMATE, scale=x_scale),
        y=y_enc(),
        tooltip=[
            alt.Tooltip(group_f, title=GROUP),
            alt.Tooltip(est_f, title=ESTIMATE),
            alt.Tooltip(low_f, title=LOWER),
            alt.Tooltip(up_f, title=UPPER),
        ],
    )
)

intervals = (
    alt.Chart(df)
    .mark_rule(strokeWidth=2, color=BRAND)
    .encode(x=alt.X(low_f, type="quantitative", scale=x_scale), x2=alt.X2(up_f), y=y_enc())
)

caps = (
    alt.Chart(df)
    .transform_fold([LOWER, UPPER], as_=["bound", "bound_value"])
    .mark_tick(thickness=2, size=14, color=BRAND)
    .encode(x=alt.X("bound_value:Q", scale=x_scale), y=y_enc())
)

reference = (
    alt.Chart(pd.DataFrame({"x": [NULL_VALUE]}))
    .mark_rule(strokeDash=[6, 3], strokeWidth=1.5, color=REFERENCE_COLOR)
    .encode(x=alt.X("x:Q", scale=x_scale))
)

chart = (
    alt.layer(reference, intervals, caps, points)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("point-basic · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_axis(
        labelFontSize=12,
        titleFontSize=14,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=1)
    .configure_title(color=INK)
)

# Save: PNG padded (never cropped) to the 3200 x 1800 target
TW, TH = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
