"""anyplot.ai
map-route-path: Route Path Map
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito positions for start/end markers
START_COLOR = "#009E73"  # position 1 — green
END_COLOR = "#D55E00"  # position 2 — vermillion

# Data: Simulated hiking trail GPS track (San Francisco coastal path)
np.random.seed(42)
n_points = 150

t = np.linspace(0, 4 * np.pi, n_points)
lon = -122.4 + 0.03 * t / (4 * np.pi) + 0.008 * np.sin(2 * t) + np.cumsum(np.random.randn(n_points) * 0.0003)
lat = 37.75 + 0.025 * np.sin(t) + 0.015 * np.cos(1.5 * t) + np.cumsum(np.random.randn(n_points) * 0.0003)
sequence = np.arange(n_points)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Line segments with viridis gradient encoding trail progression
points = np.array([lon, lat]).T.reshape(-1, 1, 2)
segments = np.concatenate([points[:-1], points[1:]], axis=1)
norm = plt.Normalize(sequence.min(), sequence.max())
lc = LineCollection(segments, cmap="viridis", norm=norm, linewidth=2.5, alpha=0.9)
lc.set_array(sequence[:-1])
line = ax.add_collection(lc)

# Colorbar
cbar = fig.colorbar(line, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Trail Progress", fontsize=10, color=INK_SOFT)
cbar.ax.tick_params(labelsize=8, labelcolor=INK_SOFT, color=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Start and end markers (Okabe-Ito positions 1 and 2)
ax.scatter(
    lon[0], lat[0], s=150, c=START_COLOR, marker="o", edgecolors=PAGE_BG, linewidths=1.5, zorder=5, label="Start"
)
ax.scatter(lon[-1], lat[-1], s=150, c=END_COLOR, marker="s", edgecolors=PAGE_BG, linewidths=1.5, zorder=5, label="End")

# Direction arrows at intervals along the path
arrow_indices = np.linspace(20, n_points - 20, 5, dtype=int)
for i in arrow_indices:
    dx = lon[i + 1] - lon[i - 1]
    dy = lat[i + 1] - lat[i - 1]
    ax.annotate(
        "",
        xy=(lon[i] + dx * 0.3, lat[i] + dy * 0.3),
        xytext=(lon[i], lat[i]),
        arrowprops={"arrowstyle": "->", "color": INK, "lw": 2.0},
    )

# Style
ax.set_xlabel("Longitude (°)", fontsize=10, color=INK)
ax.set_ylabel("Latitude (°)", fontsize=10, color=INK)
ax.set_title("map-route-path · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Suppress offset notation so full coordinate values are shown
ax.ticklabel_format(useOffset=False, style="plain")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.grid(True, alpha=0.12, linewidth=0.6, color=INK)

leg = ax.legend(fontsize=8, loc="upper left")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

x_margin = (lon.max() - lon.min()) * 0.1
y_margin = (lat.max() - lat.min()) * 0.1
ax.set_xlim(lon.min() - x_margin, lon.max() + x_margin)
ax.set_ylim(lat.min() - y_margin, lat.max() + y_margin)

plt.tight_layout()

# Save — no bbox_inches so figsize×dpi gives exact 3200×1800
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
