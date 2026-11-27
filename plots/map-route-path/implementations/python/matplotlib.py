"""anyplot.ai
map-route-path: Route Path Map
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
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
    [(0.0, "#009E73"), (0.687, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#6F7E20"), (0.21, "#009E73"), (1.0, "#CDD9FF")]
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
x0, x1 = lon.min() - x_margin, lon.max() + x_margin
y0, y1 = lat.min() - y_margin, lat.max() + y_margin
ax.set_xlim(x0, x1)
ax.set_ylim(y0, y1)

# Quiet basemap under the route: bay on the west edge, a park, and a street grid
shore_y = np.linspace(y0, y1, 60)
shore_x = lon.min() - 0.03 * (x1 - x0) + 0.004 * (x1 - x0) * np.sin(shore_y * 900)
ax.fill_betweenx(shore_y, x0, shore_x, color=INK, alpha=0.07, linewidth=0, zorder=0)
ax.plot(shore_x, shore_y, color=INK_SOFT, alpha=0.35, linewidth=0.8, zorder=0.5)
park_cx, park_cy = x0 + 0.62 * (x1 - x0), y0 + 0.5 * (y1 - y0)
park = plt.Rectangle(
    (park_cx, park_cy), 0.16 * (x1 - x0), 0.07 * (y1 - y0), color=IMPRINT_PALETTE[0], alpha=0.10, linewidth=0, zorder=0
)
ax.add_patch(park)
for gx in np.arange(shore_x.max() + 0.02 * (x1 - x0), x1, (x1 - x0) / 14):
    ax.plot([gx, gx], [y0, y1], color=INK, alpha=0.09, linewidth=0.6, zorder=0.4)
for gy in np.arange(y0, y1, (y1 - y0) / 24):
    ax.plot([shore_x.max(), x1], [gy, gy], color=INK, alpha=0.09, linewidth=0.6, zorder=0.4)
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


leg = ax.legend(fontsize=8, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)


ax.xaxis.set_major_locator(plt.MaxNLocator(3))

# Save — no bbox_inches so figsize×dpi gives exact 2400×2400
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
