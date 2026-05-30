""" anyplot.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: altair 6.1.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-30
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Mandelbrot set with smooth escape-time coloring (eliminates discrete banding)
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
max_iter = 100
nx, ny = 800, 600

step_x = (x_max - x_min) / nx
step_y = (y_max - y_min) / ny
real = np.linspace(x_min, x_max, nx, endpoint=False)
imag = np.linspace(y_min, y_max, ny, endpoint=False)
real_grid, imag_grid = np.meshgrid(real, imag)
c = real_grid + 1j * imag_grid

z = np.zeros_like(c)
smooth_iter = np.zeros(c.shape, dtype=float)
escaped = np.zeros(c.shape, dtype=bool)

for i in range(max_iter):
    active = ~escaped
    z[active] = z[active] ** 2 + c[active]
    newly_escaped = active & (np.abs(z) > 2)
    smooth_iter[newly_escaped] = i + 1 - np.log(np.log(np.abs(z[newly_escaped]))) / np.log(2)
    escaped[newly_escaped] = True

flat_real = real_grid.ravel()
flat_imag = imag_grid.ravel()
flat_iter = smooth_iter.ravel()
flat_escaped = escaped.ravel()

df_interior = pd.DataFrame(
    {
        "real": flat_real[~flat_escaped],
        "imaginary": flat_imag[~flat_escaped],
        "real2": flat_real[~flat_escaped] + step_x,
        "imaginary2": flat_imag[~flat_escaped] + step_y,
    }
)

df_exterior = pd.DataFrame(
    {
        "real": flat_real[flat_escaped],
        "imaginary": flat_imag[flat_escaped],
        "real2": flat_real[flat_escaped] + step_x,
        "imaginary2": flat_imag[flat_escaped] + step_y,
        "iterations": flat_iter[flat_escaped],
    }
)

# Plot
alt.data_transformers.disable_max_rows()

x_scale = alt.Scale(domain=[x_min, x_max])
y_scale = alt.Scale(domain=[y_min, y_max])

title = "heatmap-mandelbrot · python · altair · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(11, round(16 * ratio))

# Interior layer - black for points inside the Mandelbrot set
interior = (
    alt.Chart(df_interior)
    .mark_rect(color="#000000")
    .encode(x=alt.X("real:Q", scale=x_scale), x2="real2:Q", y=alt.Y("imaginary:Q", scale=y_scale), y2="imaginary2:Q")
)

# Exterior layer - Imprint sequential colormap (brand green → blue) for escape iterations
exterior = (
    alt.Chart(df_exterior)
    .mark_rect()
    .encode(
        x=alt.X("real:Q", title="Real (Re)", scale=x_scale),
        x2="real2:Q",
        y=alt.Y("imaginary:Q", title="Imaginary (Im)", scale=y_scale),
        y2="imaginary2:Q",
        color=alt.Color(
            "iterations:Q",
            scale=alt.Scale(range=["#009E73", "#4467A3"]),
            legend=alt.Legend(
                title="Escape Iterations", titleFontSize=10, labelFontSize=10, gradientLength=200, gradientThickness=15
            ),
        ),
        tooltip=[
            alt.Tooltip("real:Q", title="Real", format=".4f"),
            alt.Tooltip("imaginary:Q", title="Imaginary", format=".4f"),
            alt.Tooltip("iterations:Q", title="Iterations", format=".1f"),
        ],
    )
)

# Square canvas (2400×2400) - canonical for heatmaps; inner view 395×395 + 20px padding
chart = (
    (interior + exterior)
    .interactive()
    .properties(
        width=395,
        height=395,
        background=PAGE_BG,
        title=alt.Title(
            title,
            subtitle=["z(n+1) = z(n)² + c  ·  max 100 iterations  ·  escape radius 2"],
            fontSize=title_fontsize,
            subtitleFontSize=12,
            subtitleColor=INK_SOFT,
            anchor="start",
            offset=12,
        ),
        padding={"left": 20, "right": 20, "top": 20, "bottom": 20},
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
)

# Save - square canvas target: 2400×2400
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 2400, 2400
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
