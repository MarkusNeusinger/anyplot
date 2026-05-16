""" anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 86/100 | Created: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

np.random.seed(42)
t = np.linspace(0, 8 * np.pi, 1000)
x = 10 * np.cos(t)
y = 10 * np.sin(t)
z = t / (2 * np.pi)

fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor(PAGE_BG)

scatter = ax.plot(x, y, z, color=BRAND, linewidth=3, alpha=0.8)

ax.set_xlabel("X", fontsize=20, color=INK)
ax.set_ylabel("Y", fontsize=20, color=INK)
ax.set_zlabel("Z", fontsize=20, color=INK)
ax.set_title("line-3d-trajectory · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.xaxis.label.set_color(INK)
ax.yaxis.label.set_color(INK)
ax.zaxis.label.set_color(INK)

for spine in ax.spines.values():
    spine.set_color(INK_SOFT)

ax.grid(True, alpha=0.1, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
