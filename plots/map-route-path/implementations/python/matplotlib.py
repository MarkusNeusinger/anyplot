""" anyplot.ai
map-route-path: Route Path Map
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: start and end markers take positions 1 and 2
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for marks (a line on the page), stops of the render's theme
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", SEQ_MARKS)

# Columns: set these to your table's column names
LON = "Longitude (°)"  # role: lon
LAT = "Latitude (°)"  # role: lat
SEQUENCE = "Trail progress (waypoint)"  # role: sequence

# Data: replace this block with your own table, for example df = pd.read_csv("track.csv")
# Simulated hiking trail GPS track (San Francisco coastal path)
np.random.seed(42)
n_points = 150
t = np.linspace(0, 4 * np.pi, n_points)
df = pd.DataFrame(
    {
        LON: -122.4 + 0.03 * t / (4 * np.pi) + 0.008 * np.sin(2 * t) + np.cumsum(np.random.randn(n_points) * 0.0003),
        LAT: 37.75 + 0.025 * np.sin(t) + 0.015 * np.cos(1.5 * t) + np.cumsum(np.random.randn(n_points) * 0.0003),
        SEQUENCE: np.arange(n_points),
    }
)

# Plot: reads only df and the constants above
df = df.sort_values(SEQUENCE)
lon = df[LON].to_numpy()
lat = df[LAT].to_numpy()
sequence = df[SEQUENCE].to_numpy()

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
fig.subplots_adjust(left=0.27, right=0.90, top=0.92, bottom=0.09)
ax.set_anchor("W")
ax.set_facecolor(PAGE_BG)

# Line segments colored along the route by sequence
points = np.array([lon, lat]).T.reshape(-1, 1, 2)
segments = np.concatenate([points[:-1], points[1:]], axis=1)
norm = plt.Normalize(sequence.min(), sequence.max())
lc = LineCollection(segments, cmap=imprint_seq, norm=norm, linewidth=2.5, alpha=0.95)
lc.set_array(sequence[:-1])
line = ax.add_collection(lc)

x_margin = (lon.max() - lon.min()) * 0.1
y_margin = (lat.max() - lat.min()) * 0.1
ax.set_xlim(lon.min() - x_margin, lon.max() + x_margin)
ax.set_ylim(lat.min() - y_margin, lat.max() + y_margin)
# Colorbar: hugs the aspect-locked axes
ax.set_aspect(1 / np.cos(np.radians(lat.mean())), adjustable="box")
ax.apply_aspect()
box = ax.get_position()
cax = fig.add_axes((box.x1 + 0.03, box.y0 + 0.2 * box.height, 0.03, 0.6 * box.height))
cbar = fig.colorbar(line, cax=cax)
cbar.set_label(SEQUENCE, fontsize=10, color=INK_SOFT)
cbar.ax.tick_params(labelsize=8, labelcolor=INK_SOFT, color=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Start and end markers: different shape and color
ax.scatter(
    lon[0], lat[0], s=150, c=IMPRINT_PALETTE[0], marker="o", edgecolors=PAGE_BG, linewidths=1.5, zorder=5, label="Start"
)
ax.scatter(
    lon[-1], lat[-1], s=150, c=IMPRINT_PALETTE[1], marker="s", edgecolors=PAGE_BG, linewidths=1.5, zorder=5, label="End"
)

# Direction arrows at intervals along the path
arrow_indices = np.linspace(len(df) // 8, len(df) - 1 - len(df) // 8, 5, dtype=int)
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
ax.set_xlabel(LON, fontsize=10, color=INK)
ax.set_ylabel(LAT, fontsize=10, color=INK)
fig.suptitle("map-route-path · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.975)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Suppress offset notation so full coordinate values are shown
ax.ticklabel_format(useOffset=False, style="plain")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.grid(True, alpha=0.12, linewidth=0.6, color=INK)

leg = ax.legend(fontsize=8, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)


ax.xaxis.set_major_locator(plt.MaxNLocator(4))

# Save — no bbox_inches so figsize×dpi gives exact 2400×2400
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
