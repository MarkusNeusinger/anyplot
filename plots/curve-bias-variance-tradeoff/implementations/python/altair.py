"""anyplot.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-28
"""

import os
import sys


# Prevent self-import: this file is named altair.py, so remove its directory
# from sys.path before importing the altair package.
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p and os.path.abspath(p) != _this_dir]

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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: the four curves of the plot type and their line styles (solid, dashed, dotted)
BIAS = "Bias²"
VARIANCE = "Variance"
TOTAL = "Total Error"
IRREDUCIBLE = "Irreducible Error"
DASH = {BIAS: [1, 0], VARIANCE: [1, 0], TOTAL: [6, 3], IRREDUCIBLE: [4, 4]}

COMPLEXITY = "Model Complexity"  # role: model_complexity
ERROR = "Prediction Error"  # role: total_error
CURVE = "Curve"  # role: extra

# Data: replace this block with your own long table, for example df = pd.read_csv("curves.csv")
complexity = np.linspace(0.5, 10.0, 80)
bias_sq = 1.1 / (0.4 + complexity * 0.28)
variance = 0.032 * complexity**1.9
irreducible = np.full(len(complexity), 0.12)
curves = {BIAS: bias_sq, VARIANCE: variance, TOTAL: bias_sq + variance + irreducible, IRREDUCIBLE: irreducible}
df = pd.DataFrame(
    [
        {COMPLEXITY: float(c), ERROR: float(v), CURVE: name}
        for name, values in curves.items()
        for c, v in zip(complexity, values, strict=True)
    ]
)

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
X_FIELD, Y_FIELD, C_FIELD = (name.translate(ESCAPE) for name in (COMPLEXITY, ERROR, CURVE))

wide = df.pivot(index=COMPLEXITY, columns=CURVE, values=ERROR)
names = list(dict.fromkeys(df[CURVE]))
x_min, x_max = float(wide.index.min()), float(wide.index.max())
x_span = x_max - x_min
y_max = float(wide[TOTAL].max()) * 1.12
opt_x = float(wide[TOTAL].idxmin())
opt_y = float(wide[TOTAL].min())


def at(curve, frac):
    """Return (x, curve value) at a fraction of the x range."""
    x = x_min + frac * x_span
    return x, float(np.interp(x, wide.index, wide[curve]))


# Curve labels sit beside their own curve; offsets are fractions of the y range
bias_x, bias_y = at(BIAS, 0.07)
var_x, var_y = at(VARIANCE, 0.82)
tot_x, tot_y = at(TOTAL, 0.84)
irr_x, irr_y = at(IRREDUCIBLE, 0.40)
label_df = pd.DataFrame(
    [
        {"x": bias_x, "y": bias_y + 0.08 * y_max, "label": BIAS, "curve": BIAS, "align": "left"},
        {"x": var_x, "y": var_y - 0.12 * y_max, "label": VARIANCE, "curve": VARIANCE, "align": "left"},
        {"x": tot_x, "y": tot_y + 0.08 * y_max, "label": TOTAL, "curve": TOTAL, "align": "right"},
        {"x": irr_x, "y": irr_y + 0.05 * y_max, "label": IRREDUCIBLE, "curve": IRREDUCIBLE, "align": "left"},
    ]
)

shade_df = pd.DataFrame(
    [
        {"x0": x_min, "x1": opt_x, "y0": 0.0, "y1": y_max, "zone": "under"},
        {"x0": opt_x, "x1": x_max, "y0": 0.0, "y1": y_max, "zone": "over"},
    ]
)
zone_df = pd.DataFrame(
    [
        {"x": (x_min + opt_x) / 2, "y": y_max * 0.92, "text": "← Underfitting"},
        {"x": (opt_x + x_max) / 2, "y": y_max * 0.92, "text": "Overfitting →"},
    ]
)
opt_label_df = pd.DataFrame([{"x": opt_x + 0.015 * x_span, "y": y_max * 0.62, "text": "Optimal complexity"}])
formula_df = pd.DataFrame(
    [{"x": x_min + 0.5 * x_span, "y": y_max * 0.80, "text": f"{TOTAL} = {BIAS} + {VARIANCE} + {IRREDUCIBLE}"}]
)

x_scale = alt.Scale(domain=[x_min, x_max], nice=False)
y_scale = alt.Scale(domain=[0.0, y_max], nice=False)
color_scale = alt.Scale(domain=names, range=IMPRINT_PALETTE)
dash_scale = alt.Scale(domain=names, range=[DASH[name] for name in names])

# Layer 1: shaded zones (fixed fills, so they stay out of the lines' color scale)
shade_layer = (
    alt.Chart(shade_df)
    .mark_rect(opacity=0.07, stroke=None)
    .encode(
        x=alt.X("x0:Q", scale=x_scale),
        x2="x1:Q",
        y=alt.Y("y0:Q", scale=y_scale),
        y2="y1:Q",
        color=alt.Color(
            "zone:N",
            scale=alt.Scale(domain=["under", "over"], range=[IMPRINT_PALETTE[0], IMPRINT_PALETTE[4]]),
            legend=None,
        ),
    )
)

# Layer 2: curves
lines_layer = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.8)
    .encode(
        x=alt.X(X_FIELD, type="quantitative", title=COMPLEXITY, scale=x_scale),
        y=alt.Y(Y_FIELD, type="quantitative", title=ERROR, scale=y_scale),
        color=alt.Color(C_FIELD, type="nominal", title=CURVE, scale=color_scale, sort=None, legend=None),
        strokeDash=alt.StrokeDash(C_FIELD, type="nominal", title=CURVE, scale=dash_scale, sort=None, legend=None),
    )
)

# Layer 3: optimal complexity rule at the minimum of the total error
opt_rule_layer = (
    alt.Chart(pd.DataFrame({"x": [opt_x]}))
    .mark_rule(strokeDash=[5, 4], strokeWidth=1.5, color=INK_SOFT)
    .encode(x=alt.X("x:Q", scale=x_scale))
)

# Layer 4: direct curve labels, one per curve, in the curve's color; one text layer per alignment
label_layers = [
    alt.Chart(label_df[label_df["align"] == side])
    .mark_text(fontSize=12, fontWeight="bold", align=side)
    .encode(
        x=alt.X("x:Q", scale=x_scale),
        y=alt.Y("y:Q", scale=y_scale),
        text="label:N",
        color=alt.Color("curve:N", scale=color_scale, legend=None),
    )
    for side in label_df["align"].unique()
]

# Layers 5-7: zone labels, optimal label, formula
zone_layer = (
    alt.Chart(zone_df)
    .mark_text(fontSize=11, color=INK_MUTED, fontStyle="italic")
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale), text="text:N")
)
opt_label_layer = (
    alt.Chart(opt_label_df)
    .mark_text(fontSize=11, align="left", color=INK_SOFT)
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale), text="text:N")
)
formula_layer = (
    alt.Chart(formula_df)
    .mark_text(fontSize=12, color=INK_SOFT)
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale), text="text:N")
)

chart = (
    alt.layer(shade_layer, lines_layer, opt_rule_layer, *label_layers, zone_layer, opt_label_layer, formula_layer)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.TitleParams(
            text="curve-bias-variance-tradeoff · python · altair · anyplot.ai", fontSize=16, color=INK
        ),
    )
    .resolve_scale(color="independent")
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.12,
        labelColor=INK_SOFT,
        labelFontSize=10,
        titleColor=INK,
        titleFontSize=12,
    )
    .configure_axisX(grid=False)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Fit-to-canvas safety block: never crops
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
