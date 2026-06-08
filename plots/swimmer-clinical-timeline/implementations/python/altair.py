"""anyplot.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: altair | Python 3.13
Quality: 90/100 | Created: 2026-03-13
"""

import os
import sys


# Remove this script's directory from sys.path so 'import altair' finds the installed package
_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _dir]

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens — Imprint palette + theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — positions 1 & 2 for treatment arms
ARM_COLORS = ["#009E73", "#C475FD"]  # Arm A (Combo), Arm B (Mono)

# Event colors with semantic Imprint palette matches
event_color_map = {
    "Partial Response": "#BD8233",  # Imprint pos 4 — ochre, partial positive
    "Complete Response": "#2ABCCD",  # Imprint pos 6 — cyan, strong positive
    "Progressive Disease": "#AE3030",  # Imprint pos 5 — matte red, negative outcome
    "Ongoing": INK_MUTED,  # theme-adaptive neutral
}
event_shape_map = {
    "Partial Response": "triangle-up",
    "Complete Response": "cross",
    "Progressive Disease": "diamond",
    "Ongoing": "triangle-right",
}

# Data — simulated Phase II oncology trial, 25 patients, two treatment arms
np.random.seed(42)

n_patients = 25
patient_ids = [f"PT-{i + 1:03d}" for i in range(n_patients)]
arms = np.random.choice(["Arm A (Combo)", "Arm B (Mono)"], n_patients, p=[0.52, 0.48])
durations = np.round(np.random.uniform(4, 48, n_patients), 1)
durations = np.sort(durations)[::-1]
ongoing_mask = np.random.choice([True, False], n_patients, p=[0.3, 0.7])

events_list = []
for i, pid in enumerate(patient_ids):
    dur = durations[i]
    if dur > 8:
        pr_time = np.round(np.random.uniform(4, min(dur * 0.5, 16)), 1)
        events_list.append({"patient_id": pid, "time": pr_time, "event_type": "Partial Response"})
    if dur > 20 and np.random.random() > 0.5:
        cr_time = np.round(np.random.uniform(12, min(dur * 0.7, 30)), 1)
        events_list.append({"patient_id": pid, "time": cr_time, "event_type": "Complete Response"})
    if not ongoing_mask[i] and dur > 6:
        pd_time = np.round(dur - np.random.uniform(0, 3), 1)
        events_list.append({"patient_id": pid, "time": pd_time, "event_type": "Progressive Disease"})
    if ongoing_mask[i]:
        events_list.append({"patient_id": pid, "time": dur, "event_type": "Ongoing"})

bars_df = pd.DataFrame({"patient_id": patient_ids, "duration": durations, "arm": arms, "ongoing": ongoing_mask})
sort_order = bars_df.sort_values("duration", ascending=True)["patient_id"].tolist()

events_df = pd.DataFrame(events_list)
events_df = events_df.merge(bars_df[["patient_id", "arm"]], on="patient_id")

# Interactive arm highlight — click treatment arm in legend to focus
arm_selection = alt.selection_point(fields=["arm"], bind="legend")

# Bars — use fill (not color) so the arm legend stays separate from event color legend
bars = (
    alt.Chart(bars_df)
    .mark_bar(height=12, cornerRadiusEnd=3)
    .encode(
        x=alt.X(
            "duration:Q",
            title="Time on Study (Weeks)",
            axis=alt.Axis(titleFontSize=12, labelFontSize=10, tickSize=0, grid=True, gridOpacity=0.15, gridColor=INK),
        ),
        y=alt.Y("patient_id:N", title=None, sort=sort_order, axis=alt.Axis(labelFontSize=10, tickSize=0)),
        fill=alt.Fill(
            "arm:N",
            title="Treatment Arm",
            scale=alt.Scale(domain=["Arm A (Combo)", "Arm B (Mono)"], range=ARM_COLORS),
            legend=alt.Legend(orient="right", symbolSize=120, symbolStrokeWidth=0),
        ),
        opacity=alt.condition(arm_selection, alt.value(1.0), alt.value(0.25)),
        tooltip=["patient_id:N", "arm:N", alt.Tooltip("duration:Q", title="Weeks on Study")],
    )
    .add_params(arm_selection)
)

# Median reference line for population context
median_dur = float(np.median(durations))
rule_df = pd.DataFrame({"median": [median_dur]})
median_rule = alt.Chart(rule_df).mark_rule(strokeDash=[6, 4], strokeWidth=1.2, color=INK_SOFT).encode(x="median:Q")
median_label = (
    alt.Chart(rule_df)
    .mark_text(align="left", dx=4, dy=-8, fontSize=9, color=INK_MUTED, fontStyle="italic")
    .encode(x="median:Q", y=alt.value(0), text=alt.value(f"Median: {median_dur:.0f} wk"))
)

# Event markers — shape + color both encode event_type; Vega-Lite merges into one legend
markers = (
    alt.Chart(events_df)
    .mark_point(filled=True, size=180, stroke=PAGE_BG, strokeWidth=1.0)
    .encode(
        x=alt.X("time:Q"),
        y=alt.Y("patient_id:N", sort=sort_order),
        shape=alt.Shape(
            "event_type:N",
            title="Clinical Event",
            scale=alt.Scale(domain=list(event_shape_map.keys()), range=list(event_shape_map.values())),
            legend=alt.Legend(orient="right", symbolSize=120, symbolStrokeWidth=0),
        ),
        color=alt.Color(
            "event_type:N",
            title="Clinical Event",
            scale=alt.Scale(domain=list(event_color_map.keys()), range=list(event_color_map.values())),
            legend=alt.Legend(orient="right", symbolSize=120, symbolStrokeWidth=0),
        ),
        tooltip=["patient_id:N", "event_type:N", alt.Tooltip("time:Q", title="Week")],
        opacity=alt.condition(arm_selection, alt.value(1.0), alt.value(0.25)),
    )
)

# Title — 56 chars, below 67-char baseline, fontsize=16
title_text = "swimmer-clinical-timeline · python · altair · anyplot.ai"

chart = (
    (bars + median_rule + median_label + markers)
    .properties(
        width=480,
        height=320,
        background=PAGE_BG,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
        title=alt.Title(title_text, fontSize=16, fontWeight="normal", color=INK, anchor="start", offset=12),
    )
    .configure_view(fill=PAGE_BG, stroke=None, strokeWidth=0, continuousWidth=480, continuousHeight=320)
    .configure_axis(domainColor=INK_SOFT, tickColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
        padding=6,
        cornerRadius=3,
    )
    .configure_title(color=INK)
)

# Save PNG with scale_factor=4.0, then pad to exact 3200×1800
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
