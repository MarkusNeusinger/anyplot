"""anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 86/100 | Updated: 2026-11-23
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
X = "X"  # role: x
Y = "Y"  # role: y
Z = "Z"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("trajectory.csv")
t = np.linspace(0, 8 * np.pi, 1000)
df = pd.DataFrame({X: 10 * np.cos(t), Y: 10 * np.sin(t), Z: t / (2 * np.pi)})

# Plot: reads only df and the constants above
fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor(PAGE_BG)

ax.plot(df[X], df[Y], df[Z], color=IMPRINT_PALETTE[0], linewidth=2, alpha=0.8)

# Style
ax.set_xlabel(X, fontsize=10, color=INK)
ax.set_ylabel(Y, fontsize=10, color=INK)
ax.set_zlabel(Z, fontsize=10, color=INK)
ax.set_title("line-3d-trajectory · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.grid(True, alpha=0.1, color=INK)

fig.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.02)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
