"""pyplots.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-03
"""

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

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor="black")
fig.patch.set_facecolor("black")

img = ax.imshow(
    iterations,
    extent=[x_min, x_max, y_min, y_max],
    origin="lower",
    cmap="inferno",
    aspect="equal",
    interpolation="bilinear",
)

ax.set_facecolor("black")

# Colorbar
cbar = fig.colorbar(img, ax=ax, fraction=0.03, pad=0.02)
cbar.set_label("Escape Iterations", fontsize=18, color="white")
cbar.ax.tick_params(labelsize=14, colors="white")
cbar.outline.set_edgecolor("white")

# Style
text_color = "white"
ax.set_xlabel("Real Axis", fontsize=20, color=text_color)
ax.set_ylabel("Imaginary Axis", fontsize=20, color=text_color)
ax.set_title("heatmap-mandelbrot · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", color=text_color)
ax.tick_params(axis="both", labelsize=16, colors=text_color)
for spine in ax.spines.values():
    spine.set_edgecolor(text_color)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="black")
