"""anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: altair 6.1.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-21
"""

import os
import sys


sys.path = sys.path[1:]  # prevent self-import when script is named altair.py

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
SKEW_FACTOR = 40  # degrees C of rightward shift per decade of pressure (45-degree isotherms)
P_REF = 1000  # reference pressure of the skew and of the potential temperature, hPa
X_MARGIN = 5  # reference lines are pre-filtered to the x domain plus this margin (vl-convert layout)
ISOTHERMS = np.arange(-80, 50, 10)  # degrees C
DRY_THETAS = np.arange(250, 450, 20)  # K
MOIST_THETAS = np.arange(280, 380, 20)  # K
MIXING_RATIOS = [1, 2, 4, 7, 10, 15, 20]  # g/kg
LABELS = ["Temperature", "Dewpoint", "Isotherm", "Dry Adiabat", "Moist Adiabat", "Mixing Ratio"]
DASHES = [[1, 0], [8, 4], [4, 4], [1, 0], [6, 3], [2, 2]]

# Columns: set these to your table's column names
PRESSURE = "Pressure (hPa)"  # role: pressure
TEMPERATURE = "Temperature (°C)"  # role: temperature
DEWPOINT = "Dewpoint (°C)"  # role: dewpoint
SKEWED = "Temperature (°C, skewed)"  # role: extra
LABEL = "Series"  # role: extra
LINE_ID = "Line"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("sounding.csv")
df = pd.DataFrame(
    {
        PRESSURE: [1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100],
        TEMPERATURE: [25, 20, 15, 5, -15, -28, -45, -52, -55, -55, -55],
        DEWPOINT: [18, 15, 10, -5, -25, -38, -55, -62, -70, -75, -80],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})


def skew(temp_c, p_hpa):
    """Shift a temperature right by SKEW_FACTOR per decade of pressure above P_REF."""
    return temp_c + (np.log10(P_REF) - np.log10(p_hpa)) * SKEW_FACTOR


p_top, p_bottom = df[PRESSURE].min(), df[PRESSURE].max()
temp_skewed = skew(df[TEMPERATURE], df[PRESSURE])
dew_skewed = skew(df[DEWPOINT], df[PRESSURE])
x_domain = [float(np.floor(dew_skewed.min() - 8)), float(np.ceil(temp_skewed.max() + 35))]
y_scale = alt.Scale(type="log", domain=[p_bottom, p_top])

# Unified color/dash scheme: one legend covers all six element types
full_color_scale = alt.Scale(domain=LABELS, range=IMPRINT_PALETTE[: len(LABELS)])
full_dash_scale = alt.Scale(type="ordinal", domain=LABELS, range=DASHES)

# Reference lines, pre-filtered to the x domain plus margin
levels = np.linspace(p_top, p_bottom, 50)
ref_records = []


def add_line(label, line_id, temps, pressures):
    sk = skew(temps, pressures)
    keep = (sk >= x_domain[0] - X_MARGIN) & (sk <= x_domain[1] + X_MARGIN)
    for sk_i, p_i in zip(sk[keep], pressures[keep], strict=True):
        ref_records.append({PRESSURE: p_i, SKEWED: sk_i, LABEL: label, LINE_ID: line_id})


for t in ISOTHERMS:
    add_line("Isotherm", f"iso_{t}", np.full_like(levels, t, dtype=float), levels)
for theta in DRY_THETAS:
    add_line("Dry Adiabat", f"dry_{theta}", theta * (levels / P_REF) ** 0.286 - 273.15, levels)
for theta_e in MOIST_THETAS:
    add_line("Moist Adiabat", f"moist_{theta_e}", theta_e * (levels / P_REF) ** 0.23 - 273.15, levels)
mix_levels = np.linspace(max(p_top, 0.4 * p_bottom), p_bottom, 30)
for w in MIXING_RATIOS:
    e = (w * mix_levels) / (622 + w)
    ln_e = np.log(e / 6.112)
    add_line("Mixing Ratio", f"mix_{w}", 243.5 * ln_e / (17.67 - ln_e), mix_levels)
ref_df = pd.DataFrame(ref_records)

# Sounding profiles in long form, same label field for the unified scales
prof_df = pd.concat(
    [
        pd.DataFrame({PRESSURE: df[PRESSURE], SKEWED: temp_skewed, LABEL: "Temperature"}),
        pd.DataFrame({PRESSURE: df[PRESSURE], SKEWED: dew_skewed, LABEL: "Dewpoint"}),
    ],
    ignore_index=True,
)


def x_enc(**kwargs):
    return alt.X(SKEWED.translate(ESCAPE), type="quantitative", scale=alt.Scale(domain=x_domain), **kwargs)


def y_enc(**kwargs):
    return alt.Y(PRESSURE.translate(ESCAPE), type="quantitative", scale=y_scale, **kwargs)


legend = alt.Legend(title="", labelFontSize=10, titleFontSize=10, symbolSize=200, symbolStrokeWidth=2, offset=6)
color_enc = alt.Color(LABEL, type="nominal", scale=full_color_scale, legend=legend)
dash_enc = alt.StrokeDash(LABEL, type="nominal", scale=full_dash_scale, legend=None)
# Draw each profile from the surface upward instead of sorted by temperature
order_enc = alt.Order(PRESSURE.translate(ESCAPE), type="quantitative", sort="descending")

# Reference lines: thin, semi-transparent background grid
ref_lines = (
    alt.Chart(ref_df)
    .mark_line(opacity=0.40, strokeWidth=1.0)
    .encode(
        x=x_enc(title=SKEWED),
        y=y_enc(title=PRESSURE),
        detail=alt.Detail(LINE_ID, type="nominal"),
        color=color_enc,
        strokeDash=dash_enc,
    )
)

# Sounding profiles: thick lines; the legend here shows all six labels via the shared scale
prof_lines = (
    alt.Chart(prof_df)
    .mark_line(strokeWidth=3.5)
    .encode(
        x=x_enc(),
        y=y_enc(),
        color=color_enc,
        strokeDash=dash_enc,
        order=order_enc,
        tooltip=[
            alt.Tooltip(LABEL, type="nominal"),
            alt.Tooltip(PRESSURE.translate(ESCAPE), type="quantitative", title=PRESSURE),
            alt.Tooltip(SKEWED.translate(ESCAPE), type="quantitative", title=SKEWED, format=".1f"),
        ],
    )
)

# Profile points at each sounding level
prof_points = alt.Chart(prof_df).mark_circle(size=80, filled=True).encode(x=x_enc(), y=y_enc(), color=color_enc)

title_text = "skewt-logp-atmospheric · python · altair · anyplot.ai"

chart = (
    alt.layer(ref_lines, prof_lines, prof_points)
    .resolve_scale(color="shared", strokeDash="shared")
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(title_text, fontSize=16, color=INK, anchor="middle"),
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
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
    )
)

# Save PNG
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Normalise to the canonical 3200×1800 canvas, never crop (would clip title/axis labels)
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

# Save HTML
chart.save(f"plot-{THEME}.html")
