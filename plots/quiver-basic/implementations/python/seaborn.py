"""anyplot.ai
quiver-basic: Basic Quiver Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-07-24
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Imprint sequential colormap — magnitude is single-polarity (always >= 0)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Data - idealized ocean eddy current field (u = -0.1y, v = 0.1x), 20x20 grid
np.random.seed(42)
grid_size = 20
east_km = np.linspace(-30, 30, grid_size)
north_km = np.linspace(-30, 30, grid_size)
East, North = np.meshgrid(east_km, north_km)
x = East.flatten()
y = North.flatten()

u = -0.1 * y
v = 0.1 * x
magnitude = np.sqrt(u**2 + v**2)

# Scale displacement by a constant factor so arrow length stays proportional
# to magnitude (this is what makes it a true quiver plot, not a normalized one)
spacing = east_km[1] - east_km[0]
arrow_scale = (0.85 * spacing) / magnitude.max()
x_end = x + arrow_scale * u
y_end = y + arrow_scale * v

norm = plt.Normalize(magnitude.min(), magnitude.max())

# Build shaft segments for a seaborn continuous-hue lineplot, and filled
# triangular arrowheads (matplotlib patches) colored to match each shaft
head_ratio = 0.32
head_half_angle = 0.45

line_data = []
head_patches = []
for i in range(len(x)):
    mag = magnitude[i]
    if mag < 0.05:
        continue

    angle = np.arctan2(y_end[i] - y[i], x_end[i] - x[i])
    seg_length = mag * arrow_scale
    head_length = head_ratio * seg_length

    line_data.append({"x": x[i], "y": y[i], "segment": i, "order": 0, "magnitude": mag})
    line_data.append({"x": x_end[i], "y": y_end[i], "segment": i, "order": 1, "magnitude": mag})

    base_x = x_end[i] - head_length * np.cos(angle)
    base_y = y_end[i] - head_length * np.sin(angle)
    half_width = head_length * np.tan(head_half_angle)
    left = (base_x - half_width * np.sin(angle), base_y + half_width * np.cos(angle))
    right = (base_x + half_width * np.sin(angle), base_y - half_width * np.cos(angle))
    head_patches.append(([(x_end[i], y_end[i]), left, right], imprint_seq(norm(mag))))

df = pd.DataFrame(line_data)

# Plot — square canvas: the grid-based vector field has no preferred horizontal
# axis, and aspect='equal' would otherwise waste horizontal space on a 16:9 canvas
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG, constrained_layout=True)

sns.lineplot(
    data=df,
    x="x",
    y="y",
    hue="magnitude",
    hue_norm=(magnitude.min(), magnitude.max()),
    units="segment",
    estimator=None,
    sort=False,
    palette=imprint_seq,
    linewidth=1.6,
    legend=False,
    ax=ax,
)

for vertices, color in head_patches:
    ax.add_patch(Polygon(vertices, closed=True, facecolor=color, edgecolor="none"))

# Colorbar for magnitude
sm = plt.cm.ScalarMappable(cmap=imprint_seq, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Current Speed (m/s)", fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_xlabel("Distance East (km)", fontsize=10, color=INK)
ax.set_ylabel("Distance North (km)", fontsize=10, color=INK)
ax.set_title("quiver-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_aspect("equal")
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.xaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.set_xlim(-34, 34)
ax.set_ylim(-34, 34)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
