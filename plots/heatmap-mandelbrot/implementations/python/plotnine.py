""" anyplot.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-28
"""

import os
import sys


# This script is named plotnine.py which would shadow the installed package.
# Remove the script's directory from sys.path so the library is found instead.
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

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


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INTERIOR_COLOR = "#0D0D0A"  # Mandelbrot interior — near-black regardless of theme
ANNOT_COLOR = "#F0EFE8"  # near-white; annotations always on dark Mandelbrot interior

# Imprint continuous ramp for fields (cells that fill the plot), stops per theme
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# Columns
REAL = "Re(c)"  # role: extra
IMAG = "Im(c)"  # role: extra
ESCAPE = "Escape iterations"  # role: extra
LOG_ESCAPE = "Log-scaled escape iterations"  # role: extra

# Constants
MAX_ITER = 100  # escape iteration limit; the color scale is log-spaced up to this count
BAILOUT = 2**8  # large escape radius keeps the normalized iteration count continuous across the exterior

# Data: replace this block with your own grid, for example df = pd.read_csv("grid.csv")
# Mandelbrot set: z(n+1) = z(n)² + c, smooth escape-time coloring
real = np.linspace(-2.5, 1.0, 1200)
imag = np.linspace(-1.25, 1.25, 857)
real_grid, imag_grid = np.meshgrid(real, imag)
c = real_grid + 1j * imag_grid

z = np.zeros_like(c)
escape_time = np.full(c.shape, np.nan, dtype=float)
active = np.ones(c.shape, dtype=bool)

for i in range(MAX_ITER):
    z[active] = z[active] ** 2 + c[active]
    escaped = active & (np.abs(z) > BAILOUT)
    escape_time[escaped] = i + 1 - np.log2(np.log2(np.abs(z[escaped])) / np.log2(BAILOUT))
    active[escaped] = False

# Interior points (never escape) stay NaN → na_value renders them as INTERIOR_COLOR
df = pd.DataFrame({REAL: real_grid.ravel(), IMAG: imag_grid.ravel(), ESCAPE: np.clip(escape_time, 0, MAX_ITER).ravel()})

# Plot
# Log-transform escape time so the color gradient spreads across the boundary region.
# Without this, most exterior pixels (escape ≈ 1–5) collapse into a uniform flat green.
df[LOG_ESCAPE] = np.log1p(df[ESCAPE]) / np.log1p(MAX_ITER)

# 3 colorbar breaks evenly spaced in log space → labeled with original iteration counts.
log_breaks = [0.0, 0.5, 1.0]
break_labels = [str(round(np.expm1(v * np.log1p(MAX_ITER)))) for v in log_breaks]

title = "heatmap-mandelbrot · python · plotnine · anyplot.ai"

plot = (
    ggplot(df, aes(x=REAL, y=IMAG, fill=LOG_ESCAPE))
    + geom_raster(interpolate=True)
    + scale_fill_gradientn(
        colors=[c for _, c in SEQ_FIELDS],
        values=[p for p, _ in SEQ_FIELDS],
        limits=(0, 1),
        name="Escape\nIterations",
        na_value=INTERIOR_COLOR,
        breaks=log_breaks,
        labels=break_labels,
    )
    + guides(fill=guide_colorbar(nbin=300))
    + coord_fixed(ratio=1.0)
    + scale_x_continuous(expand=(0, 0))
    + scale_y_continuous(expand=(0, 0))
    + annotate("text", x=-0.25, y=0, label="Cardioid", color=ANNOT_COLOR, size=9, alpha=0.85, fontstyle="italic")
    + annotate(
        "text",
        x=-1.0,
        y=0,
        label="Period-2\nBulb",
        color=ANNOT_COLOR,
        size=9,
        alpha=0.85,
        fontstyle="italic",
        ha="center",
    )
    + labs(title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, weight="bold", ha="center", color=INK),
        axis_title_x=element_text(size=10, color=INK),
        axis_title_y=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_ticks=element_blank(),
        legend_title=element_text(size=8, weight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_position="right",
        legend_key_height=60,
        legend_key_width=12,
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=INTERIOR_COLOR),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_margin=0.02,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
