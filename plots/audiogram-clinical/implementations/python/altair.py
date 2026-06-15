""" anyplot.ai
audiogram-clinical: Clinical Audiogram
Library: altair 6.2.1 | Python 3.13.13
Quality: 87/100 | Updated: 2026-06-15
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Clinical convention (semantic exception): red=right ear, blue=left ear —
# universally recognised audiology symbols; not the default Imprint order.
RIGHT_COLOR = "#AE3030"  # Imprint position 5 (matte red)
LEFT_COLOR = "#4467A3"  # Imprint position 3 (blue)

# Imprint palette — first 6 positions used for severity band fills at low opacity
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data — bilateral high-frequency sensorineural notch (classic noise-induced pattern)
# Notch peaks at 4 kHz, partial recovery at 8 kHz; low frequencies largely intact
frequencies = [125, 250, 500, 1000, 2000, 4000, 8000]
right_thresholds = [10, 10, 15, 20, 35, 65, 55]
left_thresholds = [15, 15, 20, 25, 40, 70, 60]

right_df = pd.DataFrame({"frequency": frequencies, "threshold": right_thresholds, "ear": "Right Ear (O)"})
left_df = pd.DataFrame({"frequency": frequencies, "threshold": left_thresholds, "ear": "Left Ear (X)"})
df = pd.concat([right_df, left_df], ignore_index=True)

# Severity band boundaries (dB HL)
band_rows = [
    {"y": -10, "y2": 25, "label": "Normal"},
    {"y": 25, "y2": 40, "label": "Mild"},
    {"y": 40, "y2": 55, "label": "Moderate"},
    {"y": 55, "y2": 70, "label": "Mod. Severe"},
    {"y": 70, "y2": 90, "label": "Severe"},
    {"y": 90, "y2": 120, "label": "Profound"},
]
band_data = pd.DataFrame(band_rows)
band_data["mid_y"] = (band_data["y"] + band_data["y2"]) / 2
band_data["x_label"] = 7000  # place labels near right edge (log scale)

bands_domain = band_data["label"].tolist()

# Shared scales
x_scale = alt.Scale(type="log", domain=[125, 8000])
y_scale = alt.Scale(domain=[-10, 120], reverse=True)

x_axis = alt.Axis(
    title="Frequency (Hz)",
    values=[125, 250, 500, 1000, 2000, 4000, 8000],
    labelExpr="datum.value >= 1000 ? (datum.value / 1000) + 'k' : datum.value",
)
y_axis = alt.Axis(title="Hearing Level (dB HL)", values=list(range(-10, 121, 10)))

# Severity bands — rect marks spanning the full view width (no x/x2 = full-width fill)
bands = (
    alt.Chart(band_data)
    .mark_rect(opacity=0.15)
    .encode(
        y=alt.Y("y:Q", scale=y_scale),
        y2="y2:Q",
        color=alt.Color("label:N", scale=alt.Scale(domain=bands_domain, range=IMPRINT_PALETTE), legend=None),
    )
)

# Severity band labels positioned near the right edge of the plot
band_labels = (
    alt.Chart(band_data)
    .mark_text(align="right", fontSize=9, fontStyle="italic")
    .encode(
        x=alt.X("x_label:Q", scale=x_scale),
        y=alt.Y("mid_y:Q", scale=y_scale),
        text="label:N",
        color=alt.value(INK_MUTED),
    )
)

# Shared color / shape encoding for ears
ear_domain = ["Right Ear (O)", "Left Ear (X)"]
color_scale_ears = alt.Scale(domain=ear_domain, range=[RIGHT_COLOR, LEFT_COLOR])
shape_scale_ears = alt.Scale(domain=ear_domain, range=["circle", "cross"])

legend_cfg = alt.Legend(
    title="",
    orient="top-right",
    fillColor=ELEVATED_BG,
    strokeColor=INK_SOFT,
    labelColor=INK_SOFT,
    labelFontSize=10,
    symbolSize=150,
    symbolStrokeWidth=2.5,
)

# Connecting lines per ear (solid)
lines_layer = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X("frequency:Q", scale=x_scale, axis=x_axis),
        y=alt.Y("threshold:Q", scale=y_scale, axis=y_axis),
        color=alt.Color("ear:N", scale=color_scale_ears, legend=None),
        detail="ear:N",
    )
)

# Markers: circle (O) for right ear, cross (X) for left ear
points_layer = (
    alt.Chart(df)
    .mark_point(size=200, strokeWidth=2.5, filled=False)
    .encode(
        x=alt.X("frequency:Q", scale=x_scale),
        y=alt.Y("threshold:Q", scale=y_scale),
        color=alt.Color("ear:N", scale=color_scale_ears, legend=legend_cfg),
        shape=alt.Shape("ear:N", scale=shape_scale_ears, legend=None),
        tooltip=[
            alt.Tooltip("frequency:Q", title="Frequency (Hz)"),
            alt.Tooltip("threshold:Q", title="Threshold (dB HL)"),
            alt.Tooltip("ear:N", title="Ear"),
        ],
    )
)

title_text = "audiogram-clinical · python · altair · anyplot.ai"

# Compose layered chart
chart = (
    alt.layer(bands, band_labels, lines_layer, points_layer)
    .resolve_scale(color="independent")
    .properties(
        width=500,
        height=460,
        background=PAGE_BG,
        title=alt.Title(title_text, fontSize=16, color=INK),
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=1, continuousWidth=500, continuousHeight=460)
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
    .configure_title(color=INK, fontSize=16)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
    )
    .interactive()
)

# Save PNG and HTML
TW, TH = 2400, 2400

chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# PAD-only to exact canvas target (never crop — would trigger AR-09 edge-clip reject)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _bg_hex = PAGE_BG.lstrip("#")
    _bg_rgb = tuple(int(_bg_hex[i : i + 2], 16) for i in (0, 2, 4))
    _canvas = Image.new("RGB", (TW, TH), _bg_rgb)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
