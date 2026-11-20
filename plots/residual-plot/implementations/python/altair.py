""" anyplot.ai
residual-plot: Residual Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-20
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
OUTLIER_SIGMAS = 2  # residuals beyond this many standard deviations count as outliers

# Columns: set these to your table's column names
Y_TRUE = "Observed price ($)"  # role: y_true
Y_PRED = "Fitted price ($)"  # role: y_pred
RESIDUAL = "Residual ($)"  # role: extra
GROUP = "Point type"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
rng = np.random.default_rng(42)
house_size = np.linspace(1000, 3000, 150)  # square feet
df = pd.DataFrame(
    {
        Y_TRUE: 50000 + 150 * house_size + 0.02 * (house_size - 2000) ** 2 + rng.normal(0, 15000, house_size.size),
        Y_PRED: 50000 + 155 * house_size,  # linear model, blind to the slight curvature
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
df[RESIDUAL] = df[Y_TRUE] - df[Y_PRED]
band = OUTLIER_SIGMAS * df[RESIDUAL].std(ddof=0)
normal_label = "Normal"
outlier_label = f"Outlier (>{OUTLIER_SIGMAS}σ)"
df[GROUP] = np.where(df[RESIDUAL].abs() > band, outlier_label, normal_label)

x_enc = alt.X(Y_PRED.translate(ESCAPE), type="quantitative", title=Y_PRED, scale=alt.Scale(nice=True, zero=False))
y_enc = alt.Y(RESIDUAL.translate(ESCAPE), type="quantitative", title=RESIDUAL, scale=alt.Scale(nice=True))

scatter = (
    alt.Chart(df)
    .mark_point(size=50, opacity=0.7, filled=True)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            GROUP.translate(ESCAPE),
            type="nominal",
            title=GROUP,
            sort=None,
            scale=alt.Scale(domain=[normal_label, outlier_label], range=[IMPRINT_PALETTE[0], IMPRINT_PALETTE[4]]),
        ),
        tooltip=[
            alt.Tooltip(Y_PRED.translate(ESCAPE), title=Y_PRED, format=",.0f"),
            alt.Tooltip(RESIDUAL.translate(ESCAPE), title=RESIDUAL, format=",.0f"),
            alt.Tooltip(GROUP.translate(ESCAPE), title=GROUP),
        ],
    )
)

# Zero reference line and the horizontal bands at ±OUTLIER_SIGMAS standard deviations
zero_line = (
    alt.Chart(pd.DataFrame({RESIDUAL: [0]}))
    .mark_rule(color=INK_SOFT, strokeWidth=1.2, strokeDash=[6, 3])
    .encode(y=alt.Y(RESIDUAL.translate(ESCAPE), type="quantitative"))
)
band_lines = (
    alt.Chart(pd.DataFrame({RESIDUAL: [band, -band]}))
    .mark_rule(color=INK_SOFT, strokeWidth=0.8, strokeDash=[3, 3], opacity=0.8)
    .encode(y=alt.Y(RESIDUAL.translate(ESCAPE), type="quantitative"))
)

# LOWESS trend of the residuals along the fitted values
loess_line = (
    alt.Chart(df)
    .transform_loess(Y_PRED.translate(ESCAPE), RESIDUAL.translate(ESCAPE), bandwidth=0.3)
    .mark_line(color=INK, strokeWidth=2)
    .encode(
        x=alt.X(Y_PRED.translate(ESCAPE), type="quantitative"), y=alt.Y(RESIDUAL.translate(ESCAPE), type="quantitative")
    )
)

chart = (
    alt.layer(zero_line, band_lines, scatter, loess_line)
    .properties(
        width=580,
        height=320,
        background=PAGE_BG,
        title=alt.Title("residual-plot · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        gridOpacity=0.10,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
        orient="right",
        padding=8,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical landscape canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
