"""anyplot.ai
polar-scatter: Polar Scatter Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
COMPASS = {0: "N", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW"}

# Columns: set these to your table's column names
DIRECTION = "Wind direction (°)"  # role: theta
SPEED = "Wind speed (m/s)"  # role: radius
TIME_OF_DAY = "Time of day"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
np.random.seed(42)
df = pd.DataFrame(
    {
        DIRECTION: np.concatenate(
            [
                np.random.normal(225, 30, 40),  # morning: south-westerlies
                np.random.normal(315, 25, 40),  # afternoon: north-westerlies
                np.random.uniform(0, 360, 40),  # evening: variable winds
            ]
        )
        % 360,
        SPEED: np.concatenate([np.random.gamma(2, 3, 40), np.random.gamma(2.5, 3, 40), np.random.gamma(1.5, 3, 40)]),
        TIME_OF_DAY: ["Morning"] * 40 + ["Afternoon"] * 40 + ["Evening"] * 40,
    }
)

# Plot: reads only df and the constants above
top = (np.floor(df[SPEED].max() / 10) + 1) * 10

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, subplot_kw={"projection": "polar"}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, (group, rows) in enumerate(df.groupby(TIME_OF_DAY, sort=False)):
    ax.scatter(
        np.deg2rad(rows[DIRECTION]),
        rows[SPEED],
        color=IMPRINT_PALETTE[i],
        s=45,
        alpha=0.7,
        edgecolors=PAGE_BG,
        linewidths=0.4,
        label=group,
    )

# Angular axis: compass directions, north at the top, clockwise
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_thetagrids(list(COMPASS), labels=list(COMPASS.values()), fontsize=10, color=INK_SOFT)

# Radial axis starts at zero and reaches past the largest value
ax.set_rlim(0, top)
ax.set_rticks(np.arange(0, top + 1, 10))
ax.tick_params(axis="y", labelsize=8, colors=INK_SOFT)
ax.grid(True, alpha=0.25, linewidth=0.6, color=INK_SOFT)
ax.spines["polar"].set_color(INK_SOFT)
ax.spines["polar"].set_linewidth(0.6)

ax.set_ylabel(SPEED, fontsize=10, color=INK, labelpad=22)
ax.set_title("polar-scatter · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=14)

# Legend with marker handles at full opacity
handles = [
    Line2D([0], [0], marker="o", linestyle="", markerfacecolor=IMPRINT_PALETTE[i], markeredgecolor="none", markersize=7)
    for i in range(df[TIME_OF_DAY].nunique())
]
leg = ax.legend(
    handles=handles,
    labels=list(df[TIME_OF_DAY].unique()),
    title=TIME_OF_DAY,
    loc="upper right",
    bbox_to_anchor=(1.125, 1.12),
    fontsize=8,
    title_fontsize=9,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.6)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

fig.subplots_adjust(left=0.1, right=0.9, top=0.87, bottom=0.08)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
