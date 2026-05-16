""" anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 83/100 | Created: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Lorenz attractor
np.random.seed(42)
dt = 0.01
num_steps = 2000
x, y, z = np.zeros(num_steps), np.zeros(num_steps), np.zeros(num_steps)
x[0], y[0], z[0] = 1, 1, 1

# Lorenz attractor parameters
sigma, rho, beta = 10, 28, 8 / 3

for i in range(num_steps - 1):
    dx = sigma * (y[i] - x[i])
    dy = x[i] * (rho - z[i]) - y[i]
    dz = x[i] * y[i] - beta * z[i]

    x[i + 1] = x[i] + dt * dx
    y[i + 1] = y[i] + dt * dy
    z[i + 1] = z[i] + dt * dz

# Plot
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor(PAGE_BG)

# Plot trajectory with time-based coloring
norm = plt.Normalize(vmin=0, vmax=num_steps)
colors = plt.cm.viridis(norm(np.arange(num_steps)))

for i in range(num_steps - 1):
    ax.plot(x[i : i + 2], y[i : i + 2], z[i : i + 2], color=colors[i], linewidth=2.5)

# Style
ax.set_xlabel("X", fontsize=20, color=INK)
ax.set_ylabel("Y", fontsize=20, color=INK)
ax.set_zlabel("Z", fontsize=20, color=INK)
ax.set_title("line-3d-trajectory · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Grid styling
ax.grid(True, alpha=0.1, color=INK_SOFT)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
