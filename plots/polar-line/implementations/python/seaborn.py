""" anyplot.ai
polar-line: Polar Line Plot
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
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

# Imprint palette: all eight positions in canonical order
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
AZIMUTH = "Bearing (degrees)"  # role: theta
GAINS = ["3-element Yagi", "Cardioid"]  # role: radius

# Data: replace this block with your own table, for example df = pd.read_csv("patterns.csv")
# Two horizontal antenna gain patterns (linear power ratio) measured every 5 degrees of bearing
bearing = np.arange(0, 360, 5)


def _offset(centre):
    """Signed angular distance in degrees from `centre`, wrapped to [-180, 180)."""
    return (bearing - centre + 180) % 360 - 180


# Directional Yagi: narrow main lobe at 60 degrees, small back lobe, weak side lobes
yagi = (
    0.5
    + 9.5 * np.exp(-((_offset(60) / 22) ** 2))
    + 0.9 * np.exp(-((_offset(240) / 18) ** 2))
    + 0.6 * np.abs(np.cos(np.deg2rad(3 * (bearing - 60)))) * np.exp(-((_offset(60) / 90) ** 2))
)
# Cardioid: broad lobe at 210 degrees with a deep null behind
cardioid = 0.3 + 5.2 * ((1 + np.cos(np.deg2rad(bearing - 210))) / 2) ** 1.5

df = pd.DataFrame({AZIMUTH: bearing, GAINS[0]: yagi, GAINS[1]: cardioid})

# Plot: reads only df and the constants above
THETA = "theta_rad"

# Close each loop by repeating the first row at bearing + 360 degrees
wrap = df.head(1).copy()
wrap[AZIMUTH] = wrap[AZIMUTH] + 360
closed = pd.concat([df, wrap], ignore_index=True)
closed[THETA] = np.deg2rad(closed[AZIMUTH])

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, subplot_kw={"projection": "polar"}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

for i, series in enumerate(GAINS):
    sns.lineplot(
        data=closed, x=THETA, y=series, color=IMPRINT_PALETTE[i], label=series, sort=False, linewidth=2.2, ax=ax
    )

# Style
top = np.nanmax(df[GAINS].to_numpy())
ax.set_ylim(0, top * 1.05)
ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
ax.set_xticklabels([f"{d}°" for d in range(0, 360, 45)], fontsize=10, color=INK_SOFT)
ax.set_rlabel_position(105)
ax.tick_params(axis="y", labelsize=8, labelcolor=INK_SOFT)
ax.set_xlabel("")
ax.set_ylabel("")
ax.text(
    1.09,
    -0.09,
    "Radius: antenna gain (linear power ratio)",
    transform=ax.transAxes,
    ha="right",
    va="top",
    fontsize=10,
    color=INK_SOFT,
)
ax.grid(True, linewidth=0.8)
ax.spines["polar"].set_color(INK_SOFT)
ax.set_title(
    "Antenna Gain by Bearing · polar-line · python · seaborn · anyplot.ai",
    fontsize=12,
    fontweight="medium",
    color=INK,
    pad=22,
)
ax.legend(loc="lower left", bbox_to_anchor=(-0.09, -0.12), fontsize=8, frameon=True)
fig.subplots_adjust(left=0.1, right=0.9, top=0.86, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
