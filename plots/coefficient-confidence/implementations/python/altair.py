""" anyplot.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-18
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: brand green marks the significant coefficients, the muted anchor the rest
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
ANYPLOT_MUTED = INK_MUTED

# Constants
SIGNIFICANT_LABEL = "Significant: interval clears 0"
NOT_SIGNIFICANT_LABEL = "Not significant: interval crosses 0"

# Columns: set these to your table's column names
VARIABLE = "Predictor Variable"  # role: variable
COEFFICIENT = "Coefficient Estimate (Effect on Price, $1000s)"  # role: coefficient
CI_LOWER = "CI Lower ($1000s)"  # role: ci_lower
CI_UPPER = "CI Upper ($1000s)"  # role: ci_upper

# Data: replace this block with your own table, for example df = pd.read_csv("coefficients.csv")
estimates = np.array([45.2, 12.5, 28.7, 8.3, 0.85, 15.4, -22.1, 18.9, -5.2, 12.1, 35.6, 8.7])
std_errors = np.array([3.2, 5.8, 4.1, 3.9, 0.42, 4.2, 3.8, 2.9, 4.1, 2.8, 6.2, 3.1])
df = pd.DataFrame(
    {
        VARIABLE: [
            "Living Area (sqft)",
            "Number of Bedrooms",
            "Number of Bathrooms",
            "Lot Size (acres)",
            "Year Built",
            "Garage Capacity",
            "Distance to Downtown (mi)",
            "School Rating",
            "Property Tax Rate (%)",
            "Basement Area (sqft)",
            "Pool",
            "Central Air",
        ],
        COEFFICIENT: estimates,
        CI_LOWER: estimates - 1.96 * std_errors,  # 95 % confidence interval
        CI_UPPER: estimates + 1.96 * std_errors,
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

# A coefficient is significant when its interval does not cross zero
clears_zero = ((df[CI_LOWER] > 0) | (df[CI_UPPER] < 0)).fillna(False).astype(bool)
plot_df = df.assign(Significance=np.where(clears_zero, SIGNIFICANT_LABEL, NOT_SIGNIFICANT_LABEL))
row_order = plot_df.sort_values(COEFFICIENT, ascending=False)[VARIABLE].dropna().tolist()  # largest on top

y = alt.Y(
    VARIABLE.translate(ESCAPE),
    type="nominal",
    title=None,
    sort=row_order,
    axis=alt.Axis(labelLimit=400, ticks=False, labelPadding=8, domain=False),
)
color = alt.Color(
    "Significance",
    type="nominal",
    title=None,
    scale=alt.Scale(domain=[SIGNIFICANT_LABEL, NOT_SIGNIFICANT_LABEL], range=[BRAND, ANYPLOT_MUTED]),
    legend=alt.Legend(orient="bottom", direction="horizontal", symbolType="circle", columnPadding=28, labelLimit=400),
)
tooltip = [
    alt.Tooltip(VARIABLE.translate(ESCAPE), title=VARIABLE),
    alt.Tooltip(COEFFICIENT.translate(ESCAPE), title=COEFFICIENT, format=".2f"),
    alt.Tooltip(CI_LOWER.translate(ESCAPE), title=CI_LOWER, format=".2f"),
    alt.Tooltip(CI_UPPER.translate(ESCAPE), title=CI_UPPER, format=".2f"),
    alt.Tooltip("Significance", title="Significance"),
]

zero_line = (
    alt.Chart(pd.DataFrame({"Null effect": [0]}))
    .mark_rule(color=INK, strokeWidth=1.6, strokeDash=[6, 4])
    .encode(x=alt.X("Null effect", type="quantitative"))
)

intervals = (
    alt.Chart(plot_df)
    .mark_rule(strokeWidth=2.6, strokeCap="round")
    .encode(
        x=alt.X(CI_LOWER.translate(ESCAPE), type="quantitative", title=COEFFICIENT),
        x2=alt.X2(CI_UPPER.translate(ESCAPE)),
        y=y,
        color=color,
        tooltip=tooltip,
    )
)

estimates_marks = (
    alt.Chart(plot_df)
    .mark_point(filled=True, size=150, opacity=1, stroke=PAGE_BG, strokeWidth=1.5)
    .encode(
        x=alt.X(COEFFICIENT.translate(ESCAPE), type="quantitative", title=COEFFICIENT),
        y=y,
        color=color,
        tooltip=tooltip,
    )
)

chart = (
    alt.layer(zero_line, intervals, estimates_marks)
    .properties(
        width=560,
        height=330,
        background=PAGE_BG,
        padding={"left": 12, "right": 24, "top": 10, "bottom": 10},
        title=alt.Title("coefficient-confidence · python · altair · anyplot.ai", fontSize=16, color=INK, offset=12),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=12,
        titleFontWeight="normal",
        gridColor=INK,
        gridOpacity=0.12,
    )
    .configure_axisX(tickCount=8, titlePadding=10)
    .configure_axisY(grid=False)
    .configure_legend(labelColor=INK_SOFT, labelFontSize=11, symbolSize=120, symbolStrokeWidth=0, offset=14)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
