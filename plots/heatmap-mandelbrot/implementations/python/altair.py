"""anyplot.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-30
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (all eight positions, canonical order)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for colored fields (cells filling the plot), as (position, hex) stops
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# Constants
INTERIOR_COLOR = "#000000"  # points that never escape: one solid color, apart from every exterior color

# Columns: set these to your table's column names
REAL = "Real (Re)"  # role: extra
IMAGINARY = "Imaginary (Im)"  # role: extra
ITERATIONS = "Escape iterations"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("grid.csv")
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
max_iterations = 100
nx = 800
ny = round(nx * (y_max - y_min) / (x_max - x_min))

step = (x_max - x_min) / nx
real = x_min + step * np.arange(nx)
imag = y_min + step * np.arange(ny)
real_grid, imag_grid = np.meshgrid(real, imag)
c = real_grid + 1j * imag_grid

z = np.zeros_like(c)
smooth_iter = np.full(c.shape, np.nan)
escaped = np.zeros(c.shape, dtype=bool)
for i in range(max_iterations):
    active = ~escaped
    z[active] = z[active] ** 2 + c[active]
    newly_escaped = active & (np.abs(z) > 2)
    smooth_iter[newly_escaped] = i + 1 - np.log(np.log(np.abs(z[newly_escaped]))) / np.log(2)
    escaped[newly_escaped] = True

df = pd.DataFrame({REAL: real_grid.ravel(), IMAGINARY: imag_grid.ravel(), ITERATIONS: smooth_iter.ravel()})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
alt.data_transformers.disable_max_rows()

# Each pixel is a rect from its corner to 1.5 grid steps, so neighbours overlap and leave no anti-aliasing seams
real_step = np.diff(np.sort(df[REAL].unique())).min()
imag_step = np.diff(np.sort(df[IMAGINARY].unique())).min()
lo, hi = df[ITERATIONS].min(), df[ITERATIONS].max()
df["x2"] = df[REAL] + 1.5 * real_step
df["y2"] = df[IMAGINARY] + 1.5 * imag_step

real_field = REAL.translate(ESCAPE)
imag_field = IMAGINARY.translate(ESCAPE)
iter_field = ITERATIONS.translate(ESCAPE)
x_enc = alt.X(
    real_field,
    type="quantitative",
    title=REAL,
    scale=alt.Scale(domain=[df[REAL].min(), df[REAL].max() + real_step], nice=False, zero=False),
)
y_enc = alt.Y(
    imag_field,
    type="quantitative",
    title=IMAGINARY,
    scale=alt.Scale(domain=[df[IMAGINARY].min(), df[IMAGINARY].max() + imag_step], nice=False, zero=False),
)

title = "heatmap-mandelbrot · python · altair · anyplot.ai"
ratio = 67 / len(title) if len(title) > 67 else 1.0
title_fontsize = max(11, round(16 * ratio))

# Interior: NaN escape iterations, one solid color. Stroke in the fill color closes the seams between cells.
interior = (
    alt.Chart(df)
    .transform_filter(f"!isValid(datum['{iter_field}'])")
    .mark_rect(color=INTERIOR_COLOR, stroke=INTERIOR_COLOR, strokeWidth=0.6)
    .encode(x=x_enc, x2="x2:Q", y=y_enc, y2="y2:Q")
)

# Exterior: smooth escape iterations on the Imprint sequential ramp
exterior = (
    alt.Chart(df)
    .transform_filter(f"isValid(datum['{iter_field}'])")
    .mark_rect()
    .encode(
        x=x_enc,
        x2="x2:Q",
        y=y_enc,
        y2="y2:Q",
        fill=alt.Fill(
            iter_field,
            type="quantitative",
            title=ITERATIONS,
            scale=alt.Scale(
                domain=[lo + p * (hi - lo) for p, _ in SEQ_FIELDS],
                range=[col for _, col in SEQ_FIELDS],
                interpolate="rgb",
            ),
            legend=alt.Legend(
                type="gradient",
                orient="bottom",
                titleFontSize=12,
                labelFontSize=10,
                gradientLength=300,
                gradientThickness=14,
                direction="horizontal",
            ),
        ),
        tooltip=[
            alt.Tooltip(real_field, type="quantitative", title=REAL, format=".4f"),
            alt.Tooltip(imag_field, type="quantitative", title=IMAGINARY, format=".4f"),
            alt.Tooltip(iter_field, type="quantitative", title=ITERATIONS, format=".1f"),
        ],
    )
)

chart = (
    alt.layer(interior, exterior)
    .properties(
        width=600,
        height=600,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding={"left": 10, "right": 10, "top": 10, "bottom": 70},
        background=PAGE_BG,
        title=alt.Title(
            title,
            subtitle="z(n+1) = z(n)² + c  ·  max 100 iterations  ·  escape radius 2",
            fontSize=title_fontsize,
            subtitleFontSize=12,
            subtitleColor=INK_SOFT,
            anchor="start",
            offset=10,
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        grid=False,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=8)
    .configure_title(color=INK)
    .interactive()
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
