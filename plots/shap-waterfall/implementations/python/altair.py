"""anyplot.ai
shap-waterfall: SHAP Waterfall Plot for Feature Attribution
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-13
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

# Constants
POS_COLOR = IMPRINT_PALETTE[4]  # red: pushes the prediction up (semantic, the spec asks for red)
NEG_COLOR = IMPRINT_PALETTE[2]  # blue: pushes the prediction down
POSITIVE, NEGATIVE = "positive", "negative"

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
SHAP_VALUE = "SHAP value"  # role: shap_value
BASE_VALUE = "Base value"  # role: base_value

# Data: replace this block with your own table, for example df = pd.read_csv("shap.csv")
# Loan application: individual credit default prediction, one row per feature
df = pd.DataFrame(
    {
        FEATURE: [
            "Debt-to-Income Ratio",
            "Credit Score",
            "Annual Income",
            "Late Payments (Count)",
            "Home Ownership",
            "Employment Length",
            "Savings Balance",
            "Loan Amount",
            "Credit Utilization",
            "Credit Age (Years)",
            "Open Accounts",
            "Recent Inquiries",
        ],
        SHAP_VALUE: [0.21, 0.17, -0.14, 0.13, -0.09, 0.08, -0.06, 0.05, -0.04, -0.03, 0.02, -0.01],
        BASE_VALUE: [0.32] * 12,
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
F, S = FEATURE.translate(ESCAPE), SHAP_VALUE.translate(ESCAPE)
DIRECTION, START, END, LABEL = "Direction", "From", "To", "Label"

# Largest absolute contribution at the top, then stack cumulatively from the base value
base_value = df[BASE_VALUE].iloc[0]
data = df.reindex(df[SHAP_VALUE].abs().sort_values(ascending=False, kind="stable").index).reset_index(drop=True)
data[END] = base_value + data[SHAP_VALUE].cumsum()
data[START] = data[END] - data[SHAP_VALUE]
data[DIRECTION] = np.where(data[SHAP_VALUE] > 0, POSITIVE, NEGATIVE)
data[LABEL] = data[SHAP_VALUE].map("{:+.2f}".format)
final_value = data[END].iloc[-1]
order = data[FEATURE].tolist()
top_feature = order[0]

x_pad = 0.07
x_scale = alt.Scale(domain=[data[[START, END]].min().min() - x_pad, data[[START, END]].max().max() + x_pad])
x_enc = alt.X(f"{START}:Q", scale=x_scale, axis=alt.Axis(title="Probability of default", format=".2f"))
y_enc = alt.Y(F, type="nominal", sort=order, axis=alt.Axis(title=None, labelLimit=260))
dir_scale = alt.Scale(domain=[POSITIVE, NEGATIVE], range=[POS_COLOR, NEG_COLOR])

bars = (
    alt.Chart(data)
    .mark_bar(opacity=0.9)
    .encode(
        x=x_enc,
        x2=END,
        y=y_enc,
        color=alt.Color(
            f"{DIRECTION}:N",
            scale=dir_scale,
            legend=alt.Legend(title="SHAP direction", orient="bottom-right", offset=6),
        ),
        tooltip=[
            alt.Tooltip(F, type="nominal", title=FEATURE),
            alt.Tooltip(S, type="quantitative", title=SHAP_VALUE, format="+.3f"),
            alt.Tooltip(f"{START}:Q", title="From", format=".3f"),
            alt.Tooltip(f"{END}:Q", title="To", format=".3f"),
        ],
    )
)

# SHAP value labels beside the bar end: right of positive bars, left of negative ones
labels = alt.Chart(data).encode(
    x=alt.X(f"{END}:Q", scale=x_scale),
    y=y_enc,
    text=f"{LABEL}:N",
    color=alt.Color(f"{DIRECTION}:N", scale=dir_scale, legend=None),
)
text_pos = labels.transform_filter(alt.datum[DIRECTION] == POSITIVE).mark_text(
    align="left", dx=5, fontSize=10, fontWeight="bold"
)
text_neg = labels.transform_filter(alt.datum[DIRECTION] == NEGATIVE).mark_text(
    align="right", dx=-5, fontSize=10, fontWeight="bold"
)


def reference(value, text, dash, width, weight):
    """Reference rule at value plus its label above the top row."""
    frame = pd.DataFrame({"x": [value], FEATURE: [top_feature], "text": [text]})
    rule = (
        alt.Chart(frame)
        .mark_rule(strokeDash=dash, strokeWidth=width, opacity=0.6)
        .encode(x=alt.X("x:Q", scale=x_scale), color=alt.value(INK if weight == "bold" else INK_SOFT))
    )
    note = (
        alt.Chart(frame)
        .mark_text(align="center", dy=-22, fontSize=10, fontWeight=weight)
        .encode(
            x=alt.X("x:Q", scale=x_scale),
            y=y_enc,
            text="text:N",
            color=alt.value(INK if weight == "bold" else INK_SOFT),
        )
    )
    return rule, note


base_rule, base_note = reference(base_value, f"Base = {base_value:.2f}", [4, 3], 1, "normal")
final_rule, final_note = reference(final_value, f"Prediction = {final_value:.2f}", [], 1.5, "bold")

chart = (
    alt.layer(base_rule, final_rule, bars, text_pos, text_neg, base_note, final_note)
    .properties(
        width=620,
        height=340,
        padding={"left": 0, "right": 0, "top": 12, "bottom": 0},
        title=alt.Title("Credit Default Risk · shap-waterfall · python · altair · anyplot.ai", fontSize=16),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=None)
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
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
        padding=6,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the exact landscape canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TARGET_W or h > TARGET_H:
    raise SystemExit(f"altair produced {w}x{h}, exceeds {TARGET_W}x{TARGET_H}; shrink width/height")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - w) // 2, (TARGET_H - h) // 2))
canvas.save(f"plot-{THEME}.png")
