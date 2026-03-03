""" pyplots.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-03
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_raster,
    ggplot,
    ggsize,
    guide_colorbar,
    labs,
    scale_fill_gradientn,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Mandelbrot set computation
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
width, height = 800, 571
max_iter = 100

real = np.linspace(x_min, x_max, width)
imag = np.linspace(y_min, y_max, height)
real_grid, imag_grid = np.meshgrid(real, imag)
c = real_grid + 1j * imag_grid

z = np.zeros_like(c, dtype=complex)
iterations = np.full(c.shape, max_iter, dtype=float)

for i in range(max_iter):
    mask = np.abs(z) <= 2
    z[mask] = z[mask] ** 2 + c[mask]
    escaped = mask & (np.abs(z) > 2)
    if np.any(escaped):
        abs_z = np.abs(z[escaped])
        iterations[escaped] = i + 1 - np.log2(np.log2(abs_z))

# Interior points (never escaped) → NaN for distinct black coloring
interior = iterations >= max_iter
iterations[interior] = np.nan

df = pd.DataFrame({"real": real_grid.ravel(), "imag": imag_grid.ravel(), "iterations": iterations.ravel()})

# Plot - Mandelbrot fractal heatmap
colors = ["#000764", "#206BCB", "#EDFFFF", "#FFAA00", "#000200"]

plot = (
    ggplot(df, aes(x="real", y="imag", fill="iterations"))
    + geom_raster()
    + scale_fill_gradientn(
        colors=colors, na_value="#000000", name="Iterations", guide=guide_colorbar(barwidth=18, barheight=300, nbin=256)
    )
    + coord_fixed()
    + labs(x="Real Axis", y="Imaginary Axis", title="heatmap-mandelbrot · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold", color="#1a1a2e"),
        axis_title=element_text(size=20, color="#2d2d44"),
        axis_text=element_text(size=16, color="#2d2d44"),
        legend_title=element_text(size=16, face="bold"),
        legend_text=element_text(size=14),
        panel_grid=element_blank(),
        plot_margin=[40, 20, 20, 20],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
