"""anyplot.ai
shap-summary: SHAP Summary Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint diverging scale for feature values: low = blue, midpoint = page color, high = red
IMPRINT_DIV = ["#4467A3", PAGE_BG, "#AE3030"]

# Constants
ZERO = 0  # SHAP value where the contribution changes sign

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature_names
SHAP_VALUE = "SHAP Value (Impact on Model Output)"  # role: shap_values
FEATURE_VALUE = "Feature Value"  # role: feature_values

# Data: replace this block with your own long table, one row per sample and feature
np.random.seed(42)
n_samples = 300
feature_names = [
    "Account Age (months)",
    "Transaction Count",
    "Avg Transaction ($)",
    "Credit Score",
    "Income ($K)",
    "Debt Ratio",
    "Payment History",
    "Account Balance ($)",
    "Login Frequency",
    "Support Tickets",
]
feature_values = np.random.rand(n_samples, len(feature_names))
feature_importances = np.array([0.25, 0.20, 0.15, 0.12, 0.10, 0.07, 0.05, 0.03, 0.02, 0.01])
shap_values = np.zeros((n_samples, len(feature_names)))
for i in range(len(feature_names)):
    base_effect = (feature_values[:, i] - 0.5) * feature_importances[i] * 4
    noise = np.random.randn(n_samples) * feature_importances[i] * 0.5
    shap_values[:, i] = base_effect + noise
df = pd.DataFrame(
    {
        FEATURE: np.repeat(feature_names, n_samples),
        SHAP_VALUE: shap_values.T.ravel(),
        FEATURE_VALUE: feature_values.T.ravel(),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
F, S, V = (c.translate(ESCAPE) for c in (FEATURE, SHAP_VALUE, FEATURE_VALUE))

# Most important feature (largest mean |SHAP|) first; its rank drives the dot opacity
order = df.groupby(FEATURE)[SHAP_VALUE].apply(lambda s: s.abs().mean()).sort_values(ascending=False).index.tolist()
df["Importance rank"] = df[FEATURE].map({name: len(order) - rank for rank, name in enumerate(order)})
df["Abs SHAP"] = df[SHAP_VALUE].abs()

scatter = (
    alt.Chart(df)
    .mark_circle(stroke=INK_SOFT, strokeWidth=0.4)
    .encode(
        x=alt.X(S, type="quantitative", title=SHAP_VALUE, axis=alt.Axis(grid=True)),
        y=alt.Y(F, type="nominal", title=None, sort=order, axis=alt.Axis(ticks=False)),
        color=alt.Color(
            V,
            type="quantitative",
            title=FEATURE_VALUE,
            scale=alt.Scale(range=IMPRINT_DIV, domain=[0, 1], domainMid=0.5),
            legend=alt.Legend(orient="right", gradientLength=160, gradientThickness=14),
        ),
        opacity=alt.Opacity("Importance rank:Q", scale=alt.Scale(range=[0.55, 0.9]), legend=None),
        size=alt.Size("Abs SHAP:Q", scale=alt.Scale(range=[6, 40]), legend=None),
        yOffset=alt.YOffset("jitter:Q", scale=alt.Scale(domain=[-1, 1], range=[-12, 12])),
        tooltip=[
            alt.Tooltip(F, title=FEATURE),
            alt.Tooltip(S, type="quantitative", title=SHAP_VALUE),
            alt.Tooltip(V, type="quantitative", title=FEATURE_VALUE),
        ],
    )
    .transform_calculate(jitter="random() * 2 - 1")
)

zero_line = (
    alt.Chart(pd.DataFrame({"x": [ZERO]}))
    .mark_rule(color=INK_SOFT, strokeWidth=1.2, strokeDash=[5, 3])
    .encode(x=alt.X("x:Q"))
)

chart = (
    (zero_line + scatter)
    .properties(
        width=540,
        height=360,
        background=PAGE_BG,
        title=alt.Title("shap-summary · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        padding=6,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=11,
        labelFontSize=10,
    )
)

# Save: pad (never crop) the PNG with the page color up to the 3200 x 1800 target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair rendered {img.width}x{img.height}, larger than {TARGET_W}x{TARGET_H}; shrink the view")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
