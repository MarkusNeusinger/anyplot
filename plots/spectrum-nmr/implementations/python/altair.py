"""anyplot.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: altair | Python
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme-adaptive chrome (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Synthetic 1H NMR spectrum of ethanol (CH3-CH2-OH)
np.random.seed(42)
chemical_shift = np.linspace(-0.5, 5.0, 5000)
w = 0.012  # Lorentzian half-width

intensity = np.zeros_like(chemical_shift)

# TMS reference peak at 0 ppm (singlet)
intensity += 0.3 / (1 + ((chemical_shift - 0.0) / 0.015) ** 2)

# CH3 triplet near 1.18 ppm (3 peaks, 1:2:1 ratio, J ~ 0.07 ppm)
j_ch3 = 0.07
intensity += 0.50 / (1 + ((chemical_shift - (1.18 - j_ch3)) / w) ** 2)
intensity += 1.00 / (1 + ((chemical_shift - 1.18) / w) ** 2)
intensity += 0.50 / (1 + ((chemical_shift - (1.18 + j_ch3)) / w) ** 2)

# OH singlet near 2.61 ppm
intensity += 0.35 / (1 + ((chemical_shift - 2.61) / 0.02) ** 2)

# CH2 quartet near 3.69 ppm (4 peaks, 1:3:3:1 ratio, J ~ 0.07 ppm)
j_ch2 = 0.07
intensity += 0.25 / (1 + ((chemical_shift - (3.69 - 1.5 * j_ch2)) / w) ** 2)
intensity += 0.75 / (1 + ((chemical_shift - (3.69 - 0.5 * j_ch2)) / w) ** 2)
intensity += 0.75 / (1 + ((chemical_shift - (3.69 + 0.5 * j_ch2)) / w) ** 2)
intensity += 0.25 / (1 + ((chemical_shift - (3.69 + 1.5 * j_ch2)) / w) ** 2)

intensity += np.random.normal(0, 0.003, len(chemical_shift))
intensity = np.clip(intensity, 0, None)

df = pd.DataFrame({"Chemical Shift (ppm)": chemical_shift, "Intensity": intensity})

labels_df = pd.DataFrame(
    {
        "Chemical Shift (ppm)": [0.0, 1.18, 2.61, 3.69],
        "Intensity": [0.33, 1.08, 0.39, 0.80],
        "label": ["TMS\n0.00 ppm", "CH₃ (triplet)\n1.18 ppm", "OH (singlet)\n2.61 ppm", "CH₂ (quartet)\n3.69 ppm"],
    }
)

regions_data = pd.DataFrame(
    {
        "x_start": [-0.08, 1.02, 2.50, 3.52],
        "x_end": [0.08, 1.34, 2.72, 3.86],
        "y_start": [0.0, 0.0, 0.0, 0.0],
        "y_end": [0.38, 1.12, 0.43, 0.84],
    }
)

droplines_df = pd.DataFrame(
    {"Chemical Shift (ppm)": [0.0, 1.18, 2.61, 3.69], "y_base": [0.0, 0.0, 0.0, 0.0], "y_top": [0.30, 1.00, 0.35, 0.75]}
)

# NMR convention: high ppm on left (reversed x-axis)
x_scale = alt.Scale(domain=[5.0, -0.5])
y_scale = alt.Scale(domain=[0, 1.35])

# Nearest-point selection for interactive highlight
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["Chemical Shift (ppm)"], empty=False)

# Subtle background region shading for peak groups — theme-adaptive via BRAND
region_shading = (
    alt.Chart(regions_data)
    .mark_rect(opacity=0.08, color=BRAND, cornerRadius=3)
    .encode(x=alt.X("x_start:Q", scale=x_scale), x2="x_end:Q", y=alt.Y("y_start:Q", scale=y_scale), y2="y_end:Q")
)

# Dashed vertical drop-lines at peak centers
drop_rules = (
    alt.Chart(droplines_df)
    .mark_rule(color=BRAND, opacity=0.25, strokeDash=[4, 4], strokeWidth=1)
    .encode(x=alt.X("Chemical Shift (ppm):Q", scale=x_scale), y=alt.Y("y_base:Q", scale=y_scale), y2="y_top:Q")
)

# Spectrum line — Imprint brand green (#009E73) as first (only) series
spectrum = (
    alt.Chart(df)
    .mark_line(color=BRAND, strokeWidth=1.5)
    .encode(
        x=alt.X("Chemical Shift (ppm):Q", scale=x_scale, title="Chemical Shift (ppm)"),
        y=alt.Y("Intensity:Q", title="Intensity (a.u.)", scale=y_scale),
        tooltip=[alt.Tooltip("Chemical Shift (ppm):Q", format=".2f"), alt.Tooltip("Intensity:Q", format=".3f")],
    )
)

# Interactive crosshair rule on hover — theme-adaptive muted ink
crosshair = (
    alt.Chart(df)
    .mark_rule(color=INK_MUTED, strokeWidth=0.8, strokeDash=[3, 3])
    .encode(x=alt.X("Chemical Shift (ppm):Q", scale=x_scale))
    .transform_filter(nearest)
)

# Hover point indicator
hover_point = (
    alt.Chart(df)
    .mark_circle(size=50, color=BRAND, opacity=0.8)
    .encode(x=alt.X("Chemical Shift (ppm):Q", scale=x_scale), y=alt.Y("Intensity:Q", scale=y_scale))
    .transform_filter(nearest)
)

# Invisible voronoi layer for nearest-point selection
selectors = (
    alt.Chart(df)
    .mark_point(size=1, opacity=0)
    .encode(x=alt.X("Chemical Shift (ppm):Q", scale=x_scale))
    .add_params(nearest)
)

# Peak annotation labels — theme-adaptive ink color
peak_labels = (
    alt.Chart(labels_df)
    .mark_text(
        fontSize=11, fontWeight="bold", lineBreak="\n", align="center", dy=-18, font="Helvetica Neue, Arial, sans-serif"
    )
    .encode(
        x=alt.X("Chemical Shift (ppm):Q", scale=x_scale),
        y=alt.Y("Intensity:Q", scale=y_scale),
        text="label:N",
        color=alt.value(INK),
    )
)

chart = (
    alt.layer(region_shading, drop_rules, spectrum, selectors, crosshair, hover_point, peak_labels)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            "spectrum-nmr · altair · anyplot.ai",
            fontSize=16,
            fontWeight="bold",
            anchor="middle",
            font="Helvetica Neue, Arial, sans-serif",
            color=INK,
            subtitle="Ethanol ¹H NMR — Synthetic 300 MHz Spectrum",
            subtitleFontSize=12,
            subtitleColor=INK_SOFT,
            subtitlePadding=4,
            subtitleFont="Helvetica Neue, Arial, sans-serif",
            subtitleFontStyle="italic",
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None, continuousWidth=620, continuousHeight=320)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        titleColor=INK,
        titleFont="Helvetica Neue, Arial, sans-serif",
        titleFontWeight="normal",
        labelColor=INK_SOFT,
        labelFont="Helvetica Neue, Arial, sans-serif",
        grid=False,
        domainColor=INK_SOFT,
        domainWidth=0.8,
        tickColor=INK_SOFT,
        tickSize=5,
        tickWidth=0.8,
    )
    .configure_title(font="Helvetica Neue, Arial, sans-serif", color=INK)
    .interactive()
)

# Save PNG with vl-convert, then pad to exact 3200×1800 target
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
