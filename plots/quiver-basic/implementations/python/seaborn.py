""" anyplot.ai
quiver-basic: Basic Quiver Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 83/100 | Updated: 2026-04-29
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


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

# Data - circular rotation field (u = -y, v = x)
np.random.seed(42)
grid_size = 15
x_vals = np.linspace(-3, 3, grid_size)
y_vals = np.linspace(-3, 3, grid_size)
X, Y = np.meshgrid(x_vals, y_vals)
x = X.flatten()
y = Y.flatten()

u = -y
v = x

magnitude = np.sqrt(u**2 + v**2)

# Normalize arrow lengths for uniform display
scale = 0.15
mag_safe = np.where(magnitude > 0, magnitude, 1)
u_scaled = np.where(magnitude > 0, u / mag_safe * scale, 0)
v_scaled = np.where(magnitude > 0, v / mag_safe * scale, 0)

x_end = x + u_scaled
y_end = y + v_scaled

# Build arrow segments for seaborn lineplot
head_length = 0.05
head_angle = 0.45

line_data = []
for i in range(len(x)):
    mag = magnitude[i]
    if mag < 0.01:
        continue

    angle = np.arctan2(v_scaled[i], u_scaled[i])

    line_data.append({"x": x[i], "y": y[i], "segment": f"arrow_{i}", "order": 0, "magnitude": mag})
    line_data.append({"x": x_end[i], "y": y_end[i], "segment": f"arrow_{i}", "order": 1, "magnitude": mag})

    left_x = x_end[i] - head_length * np.cos(angle - head_angle)
    left_y = y_end[i] - head_length * np.sin(angle - head_angle)
    line_data.append({"x": x_end[i], "y": y_end[i], "segment": f"head_l_{i}", "order": 0, "magnitude": mag})
    line_data.append({"x": left_x, "y": left_y, "segment": f"head_l_{i}", "order": 1, "magnitude": mag})

    right_x = x_end[i] - head_length * np.cos(angle + head_angle)
    right_y = y_end[i] - head_length * np.sin(angle + head_angle)
    line_data.append({"x": x_end[i], "y": y_end[i], "segment": f"head_r_{i}", "order": 0, "magnitude": mag})
    line_data.append({"x": right_x, "y": right_y, "segment": f"head_r_{i}", "order": 1, "magnitude": mag})

df = pd.DataFrame(line_data)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.lineplot(
    data=df,
    x="x",
    y="y",
    hue="magnitude",
    units="segment",
    estimator=None,
    sort=False,
    palette="viridis",
    linewidth=2.5,
    legend=False,
    ax=ax,
)

# Colorbar for magnitude
norm = plt.Normalize(magnitude.min(), magnitude.max())
sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Vector Magnitude", fontsize=20, color=INK)
cbar.ax.tick_params(labelsize=16, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_xlabel("X Position", fontsize=20, color=INK)
ax.set_ylabel("Y Position", fontsize=20, color=INK)
ax.set_title("quiver-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_aspect("equal")
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.xaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.set_xlim(-3.5, 3.5)
ax.set_ylim(-3.5, 3.5)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
