""" anyplot.ai
map-route-path: Route Path Map
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
# Imprint sequential ramp for marks (stops per theme)
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", SEQ_MARKS)

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

# Constants
N_ARROWS = 4  # direction arrows spread evenly along the route

# Columns: set these to your table's column names
LON = "Longitude (°)"  # role: lon
LAT = "Latitude (°)"  # role: lat
TIME = "Elapsed Time (min)"  # role: timestamp
ELEV = "Elevation (m)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("track.csv")
# Mountain bike trail GPS track near Crested Butte, Colorado
np.random.seed(42)
n_points = 250

lat_steps = np.random.normal(0.0003, 0.0002, n_points)
lon_steps = np.random.normal(0.0004, 0.0003, n_points)
lat_steps[:80] += 0.00025
lon_steps[:80] += 0.00015
lat_steps[80:160] += 0.00010
lon_steps[80:160] -= 0.00020
lat_steps[160:] -= 0.00030
lon_steps[160:] += 0.00010

elevation = 2820 + np.cumsum(np.random.normal(0.8, 3.5, n_points)) + 120 * np.sin(np.linspace(0, 1.8 * np.pi, n_points))

df = pd.DataFrame(
    {
        LON: -106.985 + np.cumsum(lon_steps),
        LAT: 38.870 + np.cumsum(lat_steps),
        TIME: np.linspace(0, 150, n_points),
        ELEV: elevation,
    }
)

# Plot: reads only df and the constants above
fig, (ax_map, ax_elev) = plt.subplots(
    2, 1, figsize=(8, 4.5), dpi=400, gridspec_kw={"height_ratios": [3, 1]}, facecolor=PAGE_BG
)
fig.subplots_adjust(left=0.08, right=0.90, top=0.93, bottom=0.10, hspace=0.55)

# Connecting path in sequence order
sns.lineplot(data=df, x=LON, y=LAT, color=INK_SOFT, linewidth=2.8, alpha=0.75, ax=ax_map, sort=False, zorder=1)

# Waypoints colored by elapsed time
sc = ax_map.scatter(df[LON], df[LAT], c=df[TIME], cmap=imprint_seq, s=20, alpha=0.9, zorder=2, edgecolors="none")

# Start: brand green circle, ringed in ink so it stands out from the green end of the ramp
ax_map.scatter(
    df[LON].iloc[0], df[LAT].iloc[0], c=BRAND, s=300, marker="o", edgecolors=INK, linewidths=2, zorder=5, label="Start"
)

# End: purple square
ax_map.scatter(
    df[LON].iloc[-1],
    df[LAT].iloc[-1],
    c=IMPRINT_PALETTE[1],
    s=400,
    marker="s",
    edgecolors=INK,
    linewidths=2,
    zorder=5,
    label="End",
)

# Direction arrows along the path
for idx in np.linspace(len(df) * 0.2, len(df) * 0.8, N_ARROWS).astype(int):
    ax_map.annotate(
        "",
        xy=(df[LON].iloc[idx + 1], df[LAT].iloc[idx + 1]),
        xytext=(df[LON].iloc[idx], df[LAT].iloc[idx]),
        arrowprops={"arrowstyle": "->", "color": INK, "lw": 1.5},
        zorder=3,
    )

cbar = plt.colorbar(sc, ax=ax_map, pad=0.02, fraction=0.035)
cbar.set_label(TIME, fontsize=9, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
title = "Colorado Mountain Bike Trail  ·  map-route-path · python · seaborn · anyplot.ai"
ax_map.set_title(title, fontsize=round(12 * min(1.0, 67 / len(title))), fontweight="medium", color=INK)
ax_map.set_xlabel(LON, fontsize=10, color=INK)
ax_map.set_ylabel(LAT, fontsize=10, color=INK)
ax_map.tick_params(axis="both", labelsize=8)
ax_map.grid(True, alpha=0.10, linewidth=0.8)
ax_map.legend(fontsize=8, loc="lower right", framealpha=0.9, markerscale=0.5, labelspacing=1.0, borderpad=0.8)
ax_map.margins(x=0.06, y=0.12)
sns.despine(ax=ax_map)

# Elevation profile
sns.lineplot(data=df, x=TIME, y=ELEV, color=BRAND, linewidth=2.2, ax=ax_elev)
ax_elev.fill_between(df[TIME], df[ELEV].min(), df[ELEV], alpha=0.15, color=BRAND)
ax_elev.set_xlabel(TIME, fontsize=10, color=INK)
ax_elev.set_ylabel(ELEV, fontsize=10, color=INK)
ax_elev.tick_params(axis="both", labelsize=8)
ax_elev.yaxis.grid(True, alpha=0.10, linewidth=0.8)
sns.despine(ax=ax_elev)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
