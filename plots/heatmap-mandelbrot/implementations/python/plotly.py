"""anyplot.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: plotly | Python 3.13
Quality: pending | Created: 2026-05-30
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
INSIDE_COLOR = "#0D0D0A"  # near-black for points inside the Mandelbrot set

# Data: Mandelbrot set on the complex plane
# Equal x/y extents (3.5 × 3.5 units) for square canvas
x_min, x_max = -2.5, 1.0  # real axis — standard full view
y_min, y_max = -1.75, 1.75  # imaginary axis — expanded to match x extent
max_iter = 256
resolution = 1000  # square grid

real = np.linspace(x_min, x_max, resolution)
imag = np.linspace(y_min, y_max, resolution)
C = real[np.newaxis, :] + 1j * imag[:, np.newaxis]  # shape (resolution, resolution)

Z = np.zeros_like(C)
escape_count = np.zeros(C.shape, dtype=float)
escaped = np.zeros(C.shape, dtype=bool)

for i in range(max_iter):
    mask = ~escaped
    Z[mask] = Z[mask] ** 2 + C[mask]
    newly_escaped = mask & (np.abs(Z) > 2.0)
    escape_count[newly_escaped] = i + 1
    escaped |= newly_escaped

# Smooth coloring: remove discrete banding via normalized iteration count
# Z now holds the first value exceeding |z|=2 for escaped pixels
abs_z = np.abs(Z)
log_z = np.log2(np.maximum(abs_z, 1.0 + 1e-10))
log_log_z = np.log2(np.maximum(log_z, 1e-10))
smooth = np.where(escaped, escape_count - log_log_z, -1.0)

# Log-normalize escape counts to reveal color variation across the full exterior
# Linear normalization compresses most pixels near green; log spreads them evenly
s_min = smooth[escaped].min()
s_max = smooth[escaped].max()
log_norm = np.log(np.maximum(smooth - s_min + 1, 1e-10)) / np.log(s_max - s_min + 1)
z_data = np.where(escaped, log_norm * 0.98 + 0.02, 0.0)

# Colorscale: inside set = near-black; escaped = Imprint sequential (green → blue)
# imprint_seq encodes single-polarity escape iteration count
colorscale = [[0.000, INSIDE_COLOR], [0.019, INSIDE_COLOR], [0.020, "#009E73"], [1.000, "#4467A3"]]

# Plot
title = "heatmap-mandelbrot · python · plotly · anyplot.ai"
title_fontsize = round(16 * 67 / len(title)) if len(title) > 67 else 16

fig = go.Figure(
    go.Heatmap(
        z=z_data,
        x=real,
        y=imag,
        colorscale=colorscale,
        showscale=False,
        zmin=0.0,
        zmax=1.0,
        hovertemplate="Re: %{x:.3f}<br>Im: %{y:.3f}<extra></extra>",
    )
)

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=dict(l=80, r=40, t=80, b=70),
    title=dict(text=title, font=dict(size=title_fontsize, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Real Axis", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        zerolinewidth=1,
    ),
    yaxis=dict(
        title=dict(text="Imaginary Axis", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        zerolinewidth=1,
    ),
)

# Save — square canvas: 2400×2400 via width=600, height=600, scale=4
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
