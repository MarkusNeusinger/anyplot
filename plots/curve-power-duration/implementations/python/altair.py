""" anyplot.ai
curve-power-duration: Mean-Maximal Power Duration Curve
Library: altair 6.2.1 | Python 3.13.13
Quality: 89/100 | Created: 2026-06-13
"""

import sys


# This file is named altair.py; pop its directory so `import altair` finds
# the installed package rather than this script.
if sys.path and sys.path[0]:
    sys.path.pop(0)

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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series always #009E73, second always #C475FD (lavender)
BRAND = "#009E73"  # empirical MMP curve
MODEL_COLOR = "#C475FD"  # CP model fit — palette position 2

# Data — synthetic well-trained cyclist: CP = 280 W, W' = 20,000 J, Pmax = 1,100 W
# The simple CP model P=CP+W'/t diverges to ~20 kW at t=1 s (outside its valid range).
# Empirical MMP is bounded by neuromuscular ceiling (Pmax); model is shown from 1 min
# onward where it applies.
np.random.seed(42)
CP = 280
W_PRIME = 20000
P_MAX = 1100

durations = np.logspace(0, np.log10(18000), 50)  # 1 s → 5 h, log-spaced

# Empirical MMP: Pmax ceiling for short efforts, CP+W'/t decay for longer ones
empirical_power = np.minimum(P_MAX, CP + W_PRIME / durations)
noise = np.abs(np.random.normal(0, np.maximum(3, 0.02 * empirical_power)))
empirical_power = empirical_power + noise
for i in range(1, len(empirical_power)):
    empirical_power[i] = min(empirical_power[i], empirical_power[i - 1])

# CP model shown from 60 s (1 min) onward — the range where it is valid
model_mask = durations >= 60
model_durations = durations[model_mask]
model_power = CP + W_PRIME / model_durations

df = pd.concat(
    [
        pd.DataFrame({"duration_s": durations, "power_w": empirical_power, "series": "MMP Curve"}),
        pd.DataFrame({"duration_s": model_durations, "power_w": model_power, "series": "CP Model  (P = CP + W′/t)"}),
    ],
    ignore_index=True,
)

# Reference vertical markers
ref_df = pd.DataFrame({"duration_s": [5, 60, 300, 1200], "label": ["5 s", "1 min", "5 min", "20 min"]})

cp_df = pd.DataFrame({"cp": [CP]})
cp_label_df = pd.DataFrame({"x": [14000], "y": [CP + 20], "text": [f"CP = {CP} W"]})

# X-axis tick configuration
tick_vals = [1, 5, 30, 60, 300, 1200, 3600, 18000]
label_expr = (
    "datum.value === 1 ? '1 s' : "
    "datum.value === 5 ? '5 s' : "
    "datum.value === 30 ? '30 s' : "
    "datum.value === 60 ? '1 min' : "
    "datum.value === 300 ? '5 min' : "
    "datum.value === 1200 ? '20 min' : "
    "datum.value === 3600 ? '1 h' : '5 h'"
)

# Base encoding shared by line layers
base = alt.Chart(df).encode(
    x=alt.X(
        "duration_s:Q",
        scale=alt.Scale(type="log", domain=[1, 18000]),
        axis=alt.Axis(
            values=tick_vals, labelExpr=label_expr, title="Duration", titleFontSize=12, labelFontSize=10, grid=False
        ),
    ),
    y=alt.Y(
        "power_w:Q",
        scale=alt.Scale(domain=[200, 1200], clamp=True),
        axis=alt.Axis(title="Power (W)", titleFontSize=12, labelFontSize=10, grid=True),
    ),
    color=alt.Color(
        "series:N",
        scale=alt.Scale(domain=["MMP Curve", "CP Model  (P = CP + W′/t)"], range=[BRAND, MODEL_COLOR]),
        legend=alt.Legend(title=None, labelFontSize=10, symbolSize=100, orient="top-right"),
    ),
    strokeDash=alt.StrokeDash(
        "series:N",
        scale=alt.Scale(domain=["MMP Curve", "CP Model  (P = CP + W′/t)"], range=[[1, 0], [12, 4]]),
        legend=None,
    ),
    tooltip=[
        alt.Tooltip("duration_s:Q", title="Duration (s)", format=".0f"),
        alt.Tooltip("power_w:Q", title="Power (W)", format=".0f"),
        alt.Tooltip("series:N", title="Series"),
    ],
)

lines = base.mark_line(strokeWidth=3)
points_mmp = base.transform_filter('datum.series == "MMP Curve"').mark_point(size=40, filled=True)

# CP asymptote (dashed horizontal rule)
cp_rule = alt.Chart(cp_df).mark_rule(color=INK_SOFT, strokeWidth=1, strokeDash=[5, 5]).encode(y="cp:Q")

# CP label
cp_label = (
    alt.Chart(cp_label_df)
    .mark_text(align="right", baseline="bottom", fontSize=10, color=INK_MUTED)
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Reference vertical rules
ref_rules = alt.Chart(ref_df).mark_rule(color=INK_MUTED, strokeWidth=1, strokeDash=[3, 3]).encode(x="duration_s:Q")

# Reference labels at top of chart area (pixel y=6 from chart top)
ref_labels_chart = (
    alt.Chart(ref_df)
    .mark_text(baseline="top", align="center", fontSize=10, color=INK_MUTED, dy=0)
    .encode(x="duration_s:Q", text="label:N", y=alt.value(6))
)

title_text = "curve-power-duration · python · altair · anyplot.ai"

chart = (
    alt.layer(lines, points_mmp, cp_rule, cp_label, ref_rules, ref_labels_chart)
    .properties(width=620, height=320, background=PAGE_BG, title=alt.Title(title_text, fontSize=16, color=INK))
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        domainWidth=0,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.12,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(color=INK, fontSize=16)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=PAGE_BG, labelColor=INK_SOFT, titleColor=INK, labelFontSize=10)
)

# Save PNG then pad to exact target canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
