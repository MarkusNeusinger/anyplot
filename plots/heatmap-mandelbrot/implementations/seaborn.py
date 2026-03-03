""" pyplots.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-03
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Seaborn styling framework — dark palette for publication-quality fractal visualization
sns.set_theme(
    style="dark",
    rc={
        "axes.facecolor": "#000000",
        "figure.facecolor": "#060610",
        "text.color": "#d0d0d8",
        "axes.labelcolor": "#c0c0c8",
        "xtick.color": "#a0a0a8",
        "ytick.color": "#a0a0a8",
    },
)
sns.set_context("talk", font_scale=1.0)

# Data — compute Mandelbrot set with smooth escape-time coloring
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
width, height = 1000, 714
max_iter = 200
bailout = 256.0  # High bailout eliminates smooth-coloring artifacts

real = np.linspace(x_min, x_max, width)
imag = np.linspace(y_max, y_min, height)
c = real[np.newaxis, :] + 1j * imag[:, np.newaxis]

z = np.zeros_like(c)
escape_iter = np.full(c.shape, np.nan)
escaped = np.zeros(c.shape, dtype=bool)

for i in range(1, max_iter + 1):
    active = ~escaped
    z[active] = z[active] ** 2 + c[active]
    newly_escaped = active & (np.abs(z) > bailout)
    if np.any(newly_escaped):
        escaped[newly_escaped] = True
        abs_z = np.abs(z[newly_escaped])
        escape_iter[newly_escaped] = i + 1.0 - np.log2(np.log2(abs_z))

interior = ~escaped

# Seaborn-distinctive colormap — rocket palette for dramatic dark-to-bright transition
cmap = sns.color_palette("rocket", as_cmap=True)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.heatmap(
    escape_iter,
    mask=interior,
    cmap=cmap,
    robust=True,
    cbar_kws={"label": "Escape Iterations", "shrink": 0.78, "aspect": 30, "pad": 0.02, "format": "%.0f"},
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

# Labels and title with explicit sizing for legibility
ax.set_xlabel("Real Axis", fontsize=20, labelpad=14)
ax.set_ylabel("Imaginary Axis", fontsize=20, labelpad=14)
ax.set_title("heatmap-mandelbrot · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=20)

# Polished colorbar integration
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=14)
cbar.set_label("Escape Iterations", fontsize=18, labelpad=14)
cbar.outline.set_edgecolor("#2a2a35")
cbar.outline.set_linewidth(0.5)

sns.despine(ax=ax, left=True, bottom=True)

plt.tight_layout(pad=1.5)
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
