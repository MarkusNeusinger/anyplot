"""anyplot.ai
scatter-3d: 3D Scatter Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-11-19
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
PH = "Soil pH"  # role: x
CARBON = "Organic carbon (%)"  # role: y
MOISTURE = "Moisture (%)"  # role: z
LAND_USE = "Land use"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("soil.csv")
rng = np.random.default_rng(42)

# Forest: an elongated group, carbon and moisture rise together as pH drops
t = rng.uniform(0, 1, 50)
forest = pd.DataFrame(
    {
        PH: 6.4 - 1.6 * t + rng.normal(0, 0.12, 50),
        CARBON: 2.0 + 4.5 * t + rng.normal(0, 0.30, 50),
        MOISTURE: 22 + 20 * t + rng.normal(0, 1.8, 50),
        LAND_USE: "Forest",
    }
)

# Cropland: a ring in the pH-moisture plane (tilled plots at the edge of irrigated blocks)
angle = rng.uniform(0, 2 * np.pi, 50)
cropland = pd.DataFrame(
    {
        PH: 7.0 + 0.6 * np.cos(angle) + rng.normal(0, 0.07, 50),
        CARBON: 1.6 + rng.normal(0, 0.25, 50),
        MOISTURE: 20 + 7 * np.sin(angle) + rng.normal(0, 0.8, 50),
        LAND_USE: "Cropland",
    }
)

# Pasture: a compact blob
pasture = pd.DataFrame(
    {
        PH: rng.normal(5.6, 0.25, 50),
        CARBON: rng.normal(3.6, 0.40, 50),
        MOISTURE: rng.normal(34, 2.5, 50),
        LAND_USE: "Pasture",
    }
)

df = pd.concat([forest, cropland, pasture], ignore_index=True)

# Plot: reads only df and the constants above
groups = list(df[LAND_USE].unique())

fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor(PAGE_BG)

for i, group in enumerate(groups):
    subset = df[df[LAND_USE] == group]
    ax.scatter(
        subset[PH],
        subset[CARBON],
        subset[MOISTURE],
        color=IMPRINT_PALETTE[i],
        s=34,
        alpha=0.75,
        edgecolors=PAGE_BG,
        linewidth=0.3,
        label=group,
        depthshade=False,
    )

# Style
ax.set_title("scatter-3d · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=4)
ax.set_xlabel(PH, fontsize=10, labelpad=4)
ax.set_ylabel(CARBON, fontsize=10, labelpad=4)
ax.set_zlabel(MOISTURE, fontsize=10, labelpad=2)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, pad=0)
ax.tick_params(axis="z", labelsize=8, colors=INK_SOFT, pad=1)

for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.pane.set_facecolor(PAGE_BG)
    axis.pane.set_edgecolor(INK_SOFT)
    axis._axinfo["grid"]["color"] = INK
    axis._axinfo["grid"]["linewidth"] = 0.5
    axis._axinfo["grid"]["alpha"] = 0.15

ax.view_init(elev=22, azim=-58)

legend = ax.legend(title=LAND_USE, fontsize=8, title_fontsize=9, loc="upper left", bbox_to_anchor=(0.0, 0.92))
for text in legend.get_texts():
    text.set_color(INK)
legend.get_title().set_color(INK)

fig.subplots_adjust(left=0.0, right=1.0, bottom=0.02, top=0.95)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
