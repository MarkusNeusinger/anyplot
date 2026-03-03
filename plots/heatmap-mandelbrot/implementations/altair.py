"""pyplots.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: altair 6.0.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-03
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - compute Mandelbrot set with smooth coloring
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
max_iter = 100
nx, ny = 600, 428

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

# Build DataFrames for interior (in-set) and exterior (escaped) points
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

# Interior layer - black cells for points inside the Mandelbrot set
interior = (
    alt.Chart(df_interior)
    .mark_rect(color="#000000")
    .encode(x=alt.X("real:Q", scale=x_scale), x2="real2:Q", y=alt.Y("imaginary:Q", scale=y_scale), y2="imaginary2:Q")
)

# Exterior layer - colored by smooth iteration count
exterior = (
    alt.Chart(df_exterior)
    .mark_rect()
    .encode(
        x=alt.X("real:Q", title="Real (Re)", scale=x_scale, axis=alt.Axis(titleFontSize=22, labelFontSize=18)),
        x2="real2:Q",
        y=alt.Y(
            "imaginary:Q", title="Imaginary (Im)", scale=y_scale, axis=alt.Axis(titleFontSize=22, labelFontSize=18)
        ),
        y2="imaginary2:Q",
        color=alt.Color(
            "iterations:Q",
            scale=alt.Scale(scheme="plasma"),
            legend=alt.Legend(
                title="Escape Iterations", titleFontSize=18, labelFontSize=16, gradientLength=400, gradientThickness=20
            ),
        ),
        tooltip=[
            alt.Tooltip("real:Q", title="Real", format=".4f"),
            alt.Tooltip("imaginary:Q", title="Imaginary", format=".4f"),
            alt.Tooltip("iterations:Q", title="Iterations", format=".1f"),
        ],
    )
)

# Combine layers
chart = (
    (interior + exterior)
    .interactive()
    .properties(
        width=1400,
        height=1000,
        title=alt.Title("heatmap-mandelbrot · altair · pyplots.ai", fontSize=28, anchor="start", offset=16),
        padding={"left": 20, "right": 20, "top": 20, "bottom": 20},
    )
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
