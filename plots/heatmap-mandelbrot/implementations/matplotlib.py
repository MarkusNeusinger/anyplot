""" pyplots.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 93/100 | Created: 2026-03-03
"""

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np


# Data — compute Mandelbrot escape iterations
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
width, height = 1200, 860
max_iterations = 200

real = np.linspace(x_min, x_max, width)
imag = np.linspace(y_min, y_max, height)
real_grid, imag_grid = np.meshgrid(real, imag)
c = real_grid + 1j * imag_grid

z = np.zeros_like(c)
iterations = np.zeros(c.shape, dtype=float)
mask = np.ones(c.shape, dtype=bool)

for i in range(max_iterations):
    z[mask] = z[mask] ** 2 + c[mask]
    escaped = mask & (np.abs(z) > 2)
    # Smooth coloring: fractional escape count to avoid banding
    iterations[escaped] = i + 1 - np.log2(np.log2(np.abs(z[escaped])))
    mask[escaped] = False

# Points inside the set get NaN so they render as black
iterations[mask] = np.nan

# PowerNorm emphasizes boundary detail — a distinctive matplotlib normalization
norm = mcolors.PowerNorm(gamma=0.4, vmin=np.nanmin(iterations), vmax=np.nanmax(iterations))

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor="black")

img = ax.imshow(
    iterations,
    extent=[x_min, x_max, y_min, y_max],
    origin="lower",
    cmap="inferno",
    norm=norm,
    aspect="equal",
    interpolation="bilinear",
)

ax.set_facecolor("black")

# Subtle contour lines at escape boundaries for depth and visual hierarchy
iterations_clean = np.where(np.isnan(iterations), 0, iterations)
ax.contour(
    iterations_clean,
    levels=[5, 15, 35, 70, 120],
    extent=[x_min, x_max, y_min, y_max],
    colors="white",
    linewidths=0.3,
    alpha=0.12,
    origin="lower",
)

# Colorbar
cbar = fig.colorbar(img, ax=ax, fraction=0.03, pad=0.02)
cbar.set_label("Escape Iterations", fontsize=20, color="white")
cbar.ax.tick_params(labelsize=16, colors="white")
cbar.outline.set_edgecolor("#444444")

# Style — mathematical axis labels using matplotlib's mathtext rendering
text_color = "white"
ax.set_xlabel(r"Real Part $\mathrm{Re}(c)$", fontsize=20, color=text_color)
ax.set_ylabel(r"Imaginary Part $\mathrm{Im}(c)$", fontsize=20, color=text_color)
ax.set_title("heatmap-mandelbrot · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", color=text_color, pad=16)
ax.tick_params(axis="both", labelsize=16, colors=text_color)

# Clean spine removal for visual refinement
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="black")
