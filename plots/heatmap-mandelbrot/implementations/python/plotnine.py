""" pyplots.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-03
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_raster,
    ggplot,
    guide_colorbar,
    guides,
    labs,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data — Mandelbrot set: z(n+1) = z(n)² + c
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
max_iter = 100
nx, ny = 1200, 857

real = np.linspace(x_min, x_max, nx)
imag = np.linspace(y_min, y_max, ny)
real_grid, imag_grid = np.meshgrid(real, imag)
c = real_grid + 1j * imag_grid

# Vectorized iteration with smooth escape-time coloring
z = np.zeros_like(c)
escape_time = np.zeros(c.shape, dtype=float)
active = np.ones(c.shape, dtype=bool)

for i in range(max_iter):
    z[active] = z[active] ** 2 + c[active]
    escaped = active & (np.abs(z) > 2)
    escape_time[escaped] = i + 1 - np.log2(np.log2(np.abs(z[escaped])))
    active[escaped] = False

# Interior (never escapes) = 0 → maps to black in palette
escape_time[active] = 0
escape_time = np.clip(escape_time, 0, max_iter)

# Smooth the rendering artifact along y=0 (real axis) where iteration
# behavior differs slightly due to z staying purely real
y0_idx = np.argmin(np.abs(imag))
if abs(imag[y0_idx]) < 1e-10:
    escape_time[y0_idx] = (escape_time[y0_idx - 1] + escape_time[y0_idx + 1]) / 2

# Long-form DataFrame for plotnine grammar of graphics
df = pd.DataFrame({"real": real_grid.ravel(), "imag": imag_grid.ravel(), "escape": escape_time.ravel()})

# "Cosmic fire" palette — void → electric violet → hot magenta → molten gold → white
palette = [
    "#000000",  # void (set interior)
    "#140028",  # deepest purple
    "#2d0d6b",  # dark violet
    "#5b18a8",  # electric violet
    "#8c2fc2",  # bright purple
    "#c244a0",  # hot magenta
    "#e55870",  # coral pink
    "#f58040",  # tangerine
    "#fbb818",  # gold
    "#f8e868",  # bright gold
    "#fffff0",  # white glow
]
stops = [0.0, 0.01, 0.10, 0.22, 0.36, 0.50, 0.62, 0.74, 0.85, 0.94, 1.0]

# Plot — layered grammar of graphics composition
plot = (
    ggplot(df, aes(x="real", y="imag", fill="escape"))
    + geom_raster(interpolate=True)
    + scale_fill_gradientn(
        colors=palette,
        values=stops,
        limits=(0, max_iter),
        name="Escape\nIterations",
        na_value="#000000",
        breaks=[0, 25, 50, 75, 100],
    )
    + guides(fill=guide_colorbar(nbin=300))
    + coord_fixed(ratio=1.0)
    + scale_x_continuous(expand=(0, 0))
    + scale_y_continuous(expand=(0, 0))
    + annotate("text", x=-0.25, y=0, label="Cardioid", color="white", size=10, alpha=0.45, fontstyle="italic")
    + annotate(
        "text", x=-1.0, y=0, label="Period-2\nBulb", color="white", size=8, alpha=0.45, fontstyle="italic", ha="center"
    )
    + labs(x="Re(c)", y="Im(c)", title="heatmap-mandelbrot · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", ha="center"),
        axis_title_x=element_text(size=20, margin={"t": 10}),
        axis_title_y=element_text(size=20, margin={"r": 10}),
        axis_text=element_text(size=16, color="#999999"),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_key_height=50,
        legend_key_width=18,
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#000000"),
        plot_background=element_rect(fill="#0a0a0f", color="none"),
        plot_margin=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
