"""anyplot.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, PowerNorm


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint sequential colormap (single-polarity: green→blue)
cmap = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])
cmap.set_bad(color="#1A1A17")  # interior of the set stays dark on both themes

# Data — compute Mandelbrot escape iterations on the complex plane
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
width_px, height_px = 1200, 860
max_iterations = 200

real = np.linspace(x_min, x_max, width_px)
imag = np.linspace(y_min, y_max, height_px)
real_grid, imag_grid = np.meshgrid(real, imag)
c = real_grid + 1j * imag_grid

z = np.zeros_like(c)
iterations = np.zeros(c.shape, dtype=float)
mask = np.ones(c.shape, dtype=bool)

for i in range(max_iterations):
    z[mask] = z[mask] ** 2 + c[mask]
    escaped = mask & (np.abs(z) > 2)
    # Smooth coloring: fractional escape count eliminates discrete banding
    iterations[escaped] = i + 1 - np.log2(np.log2(np.abs(z[escaped])))
    mask[escaped] = False

# Points inside the set get NaN so cmap.set_bad() renders them dark
iterations[mask] = np.nan

# PowerNorm(gamma=0.4) compresses the high end, revealing more boundary detail
norm = PowerNorm(gamma=0.4, vmin=np.nanmin(iterations), vmax=np.nanmax(iterations))

# Plot — square canvas (heatmap genre)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

img = ax.imshow(
    iterations,
    extent=[x_min, x_max, y_min, y_max],
    origin="lower",
    cmap=cmap,
    norm=norm,
    aspect="equal",
    interpolation="bilinear",
)

# Subtle contour lines at escape boundaries add depth without cluttering the fractal
iterations_clean = np.where(np.isnan(iterations), 0, iterations)
ax.contour(
    iterations_clean,
    levels=[5, 15, 35, 70, 120],
    extent=[x_min, x_max, y_min, y_max],
    colors=INK_SOFT,
    linewidths=0.3,
    alpha=0.15,
    origin="lower",
)

# Colorbar
cbar = fig.colorbar(img, ax=ax, fraction=0.03, pad=0.02)
cbar.set_label("Escape Iterations", fontsize=10, color=INK_SOFT)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style — simplified axis labels remove redundancy (Re(c) not "Real Part Re(c)")
title = "heatmap-mandelbrot · python · matplotlib · anyplot.ai"
ax.set_xlabel(r"$\mathrm{Re}(c)$", fontsize=10, color=INK)
ax.set_ylabel(r"$\mathrm{Im}(c)$", fontsize=10, color=INK)
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=16)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

for spine in ax.spines.values():
    spine.set_visible(False)

fig.subplots_adjust(left=0.11, right=0.88, top=0.93, bottom=0.09)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
