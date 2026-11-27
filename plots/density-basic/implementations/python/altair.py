"""anyplot.ai
density-basic: Basic Density Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-30
"""

import importlib
import os
import sys

import numpy as np
import pandas as pd


# Drop script directory from sys.path so `altair` resolves the package, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
Image = importlib.import_module("PIL.Image")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single series, so the first position
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
BANDWIDTH = 4  # smoothing of the density estimate, in units of the value axis

# Columns: set these to your table's column names
SCORE = "Test Score (points)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
df = pd.DataFrame(
    {
        SCORE: np.clip(
            np.concatenate(
                [
                    np.random.normal(loc=38, scale=7, size=200),  # foundational course
                    np.random.normal(loc=72, scale=8, size=150),  # advanced course
                ]
            ),
            5,
            100,
        )
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
DENSITY = "Probability Density"
field = SCORE.translate(ESCAPE)
lo, hi = df[SCORE].min(), df[SCORE].max()
x_scale = alt.Scale(domain=[lo - 3 * BANDWIDTH, hi + 3 * BANDWIDTH], nice=False)
x_enc = alt.X(field, type="quantitative", title=SCORE, scale=x_scale, axis=alt.Axis(tickCount=10, grid=False))
y_enc = alt.Y(DENSITY, type="quantitative", title=DENSITY, axis=alt.Axis(format=".3f"))

# Nearest-point selection for interactive density readout (HTML export)
nearest = alt.selection_point(nearest=True, on="pointerover", fields=[SCORE], empty=False)

# Density curve, estimated by Vega-Lite and extended past the data so it falls back to zero
density = alt.Chart(df).transform_density(
    SCORE, as_=[SCORE, DENSITY], bandwidth=BANDWIDTH, extent=[lo - 3 * BANDWIDTH, hi + 3 * BANDWIDTH]
)

curve = density.mark_area(opacity=0.40, color=BRAND, line={"color": BRAND, "strokeWidth": 2.5}).encode(
    x=x_enc,
    y=y_enc,
    tooltip=[
        alt.Tooltip(field, type="quantitative", title="Score", format=".1f"),
        alt.Tooltip(DENSITY, type="quantitative", title="Density", format=".4f"),
    ],
)

# Invisible points on the curve drive the nearest-point selection, a dot marks the hovered one
hover_points = density.mark_point(opacity=0).encode(
    x=alt.X(field, type="quantitative"), y=alt.Y(DENSITY, type="quantitative")
)
hover_dot = density.mark_point(size=80, filled=True, color=BRAND).encode(
    x=alt.X(field, type="quantitative"),
    y=alt.Y(DENSITY, type="quantitative"),
    opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
)
hover_points = hover_points.add_params(nearest)

# Rug plot: one tick per observation at density 0
rug = (
    alt.Chart(df)
    .mark_tick(color=BRAND, opacity=0.3, thickness=1.5, size=14)
    .encode(x=alt.X(field, type="quantitative"), y=alt.Y(datum=0))
)

title_text = "density-basic · python · altair · anyplot.ai"
title_fs = round(16 * 67 / len(title_text)) if len(title_text) > 67 else 16

chart = (
    alt.layer(curve, rug, hover_points, hover_dot)
    .properties(
        width=800,
        height=450,
        padding=10,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        background=PAGE_BG,
        title=alt.Title(
            text=title_text,
            subtitle="Kernel density estimation of test scores across two course levels",
            fontSize=title_fs,
            subtitleFontSize=13,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
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
    .configure_title(color=INK)
)

# Save PNG at exactly 3200 x 1800 (autosize fit makes the chart fill it)
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

# Save interactive HTML with selection-driven hover readout
chart.save(f"plot-{THEME}.html")
