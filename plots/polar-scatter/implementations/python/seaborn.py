""" anyplot.ai
polar-scatter: Polar Scatter Plot
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
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
        "legend.facecolor": PAGE_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]  # 45-degree compass ticks

# Columns: set these to your table's column names
DIRECTION = "Wind direction (deg)"  # role: theta
SPEED = "Wind speed (m/s)"  # role: radius
SEASON = "Season"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
rng = np.random.default_rng(7)
n_winter, n_summer = 65, 55

# Winter: a strong, steady westerly
winter_dir = rng.normal(270, 22, n_winter) % 360
winter_speed = rng.gamma(6, 1.6, n_winter) + 3

# Summer: lighter westerlies with a weak easterly tail
easterly = rng.random(n_summer) < 0.25
summer_dir = np.where(easterly, rng.normal(85, 25, n_summer), rng.normal(255, 40, n_summer)) % 360
summer_speed = rng.gamma(4, 1.3, n_summer) + 1.5

df = pd.DataFrame(
    {
        DIRECTION: np.concatenate([winter_dir, summer_dir]),
        SPEED: np.concatenate([winter_speed, summer_speed]),
        SEASON: ["Winter"] * n_winter + ["Summer"] * n_summer,
    }
)

# Plot
fig = plt.figure(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="polar")

# Radians internally; degrees and compass points for display
theta = np.deg2rad(df[DIRECTION])
n_seasons = df[SEASON].nunique()
sns.scatterplot(
    data=df.assign(_theta=theta),
    x="_theta",
    y=SPEED,
    hue=SEASON,
    palette=IMPRINT_PALETTE[:n_seasons],
    s=40,
    alpha=0.7,
    edgecolor=PAGE_BG,
    linewidth=0.4,
    ax=ax,
)

ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
ax.set_xticklabels(COMPASS, fontsize=10, color=INK_SOFT)
ax.set_xlabel("")

ax.set_ylim(0, df[SPEED].max() * 1.1)
ax.set_rlabel_position(157.5)
ax.tick_params(axis="y", labelsize=8, colors=INK_SOFT)
ax.set_ylabel(SPEED, fontsize=10, labelpad=28)
ax.grid(True, linewidth=0.6)

ax.set_title("polar-scatter · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", pad=18, color=INK)

ax.get_legend().remove()
handles, labels = ax.get_legend_handles_labels()
legend = fig.legend(
    handles,
    labels,
    title=SEASON,
    title_fontsize=9,
    fontsize=8,
    loc="upper right",
    bbox_to_anchor=(0.99, 0.97),
    framealpha=0.9,
)
legend.get_title().set_color(INK)
for t in legend.texts:
    t.set_color(INK)

fig.subplots_adjust(left=0.1, right=0.9, top=0.88, bottom=0.08)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
