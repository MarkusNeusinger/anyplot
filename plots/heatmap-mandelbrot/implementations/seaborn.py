""" pyplots.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-03
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data — compute Mandelbrot set escape iterations on the complex plane
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
width, height = 800, 571
max_iter = 100

real = np.linspace(x_min, x_max, width)
imag = np.linspace(y_max, y_min, height)
c = real[np.newaxis, :] + 1j * imag[:, np.newaxis]

z = np.zeros_like(c)
escape_iter = np.zeros(c.shape, dtype=float)
escaped = np.zeros(c.shape, dtype=bool)

for i in range(1, max_iter + 1):
    active = ~escaped
    z[active] = z[active] ** 2 + c[active]
    newly_escaped = active & (np.abs(z) > 2)
    escaped[newly_escaped] = True
    if np.any(newly_escaped):
        log_zn = np.log2(np.abs(z[newly_escaped]))
        escape_iter[newly_escaped] = np.maximum(i + 1 - np.log2(log_zn), 0)

interior = ~escaped

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
ax.set_facecolor("black")

sns.heatmap(
    escape_iter,
    mask=interior,
    cmap="inferno",
    cbar_kws={"label": "Escape Iterations", "shrink": 0.8},
    xticklabels=False,
    yticklabels=False,
    ax=ax,
)

# Custom axis ticks for complex plane coordinates
n_xticks = 8
n_yticks = 6
ax.set_xticks(np.linspace(0, width, n_xticks))
ax.set_xticklabels([f"{v:.1f}" for v in np.linspace(x_min, x_max, n_xticks)], fontsize=16)
ax.set_yticks(np.linspace(0, height, n_yticks))
ax.set_yticklabels([f"{v:.2f}" for v in np.linspace(y_max, y_min, n_yticks)], fontsize=16)

# Style
ax.set_xlabel("Real Axis", fontsize=20, labelpad=12)
ax.set_ylabel("Imaginary Axis", fontsize=20, labelpad=12)
ax.set_title("heatmap-mandelbrot · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=16)

# Colorbar styling
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=14)
cbar.set_label("Escape Iterations", fontsize=18, labelpad=12)

sns.despine(ax=ax, left=True, bottom=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
