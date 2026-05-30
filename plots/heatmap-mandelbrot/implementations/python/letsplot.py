"""anyplot.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: letsplot | Python
Imprint palette sequential colormap: brand-green → blue.
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_raster,
    ggplot,
    ggsize,
    guide_colorbar,
    labs,
    layer_tooltips,
    scale_fill_gradient,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme-adaptive chrome (Imprint palette chrome tokens)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data — Mandelbrot set via smooth (normalized) iteration count
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
        # Smooth coloring eliminates discrete banding
        iterations[escaped] = i + 1 - np.log2(np.log2(abs_z))

# Interior points (never escaped) → NaN → na_value black
interior = iterations >= max_iter
iterations[interior] = np.nan

df = pd.DataFrame({"real": real_grid.ravel(), "imag": imag_grid.ravel(), "iterations": iterations.ravel()})

# Plot — Imprint sequential colormap (brand-green → blue) on escape-time data
plot = (
    ggplot(df, aes(x="real", y="imag", fill="iterations"))
    + geom_raster(
        tooltips=layer_tooltips()
        .format("@real", ".3f")
        .format("@imag", ".3f")
        .format("@iterations", ".1f")
        .line("c = @real + @imag·i")
        .line("Iterations: @iterations")
    )
    + scale_fill_gradient(
        low="#009E73",
        high="#4467A3",
        na_value="#000000",
        name="Iterations",
        guide=guide_colorbar(barwidth=15, barheight=200, nbin=256),
    )
    + scale_x_continuous(name="Real Axis", breaks=[-2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0], expand=[0.01, 0])
    + scale_y_continuous(name="Imaginary Axis", breaks=[-1.0, -0.5, 0.0, 0.5, 1.0], expand=[0.01, 0])
    + coord_fixed()
    + labs(
        title="heatmap-mandelbrot · letsplot · anyplot.ai",
        subtitle="Escape-time fractal with smooth iteration coloring on the complex plane",
        caption="z(n+1) = z(n)² + c · max iterations = 100 · interior points in black",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=16, face="bold", color=INK),
        plot_subtitle=element_text(size=11, color=INK_SOFT, face="italic"),
        plot_caption=element_text(size=9, color=INK_MUTED),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid=element_blank(),
        panel_background=element_rect(fill=PAGE_BG),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_margin=[20, 15, 10, 15],
    )
    + ggsize(800, 450)
)

# Save — canonical scale=4 → 3200×1800 px landscape
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
