"""anyplot.ai
bump-basic: Basic Bump Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — 8 hues, theme-independent
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DRIVER = "Driver"  # role: entity
RACE = "Grand Prix"  # role: period
POSITION = "Championship Position"  # role: rank

# Data: replace this block with your own table, for example df = pd.read_csv("standings.csv")
races = ["Bahrain", "Jeddah", "Melbourne", "Suzuka", "Shanghai", "Miami", "Imola", "Monaco"]
rankings = {
    "Verstappen": [1, 1, 1, 2, 3, 3, 2, 1],
    "Hamilton": [4, 3, 2, 1, 1, 2, 1, 2],
    "Norris": [5, 5, 4, 3, 2, 1, 3, 3],
    "Leclerc": [2, 2, 3, 4, 5, 5, 4, 4],
    "Sainz": [3, 4, 5, 5, 4, 4, 5, 5],
    "Piastri": [6, 6, 7, 7, 6, 6, 6, 7],
    "Russell": [7, 7, 6, 6, 7, 7, 7, 6],
}
df = pd.DataFrame(
    {
        DRIVER: [driver for driver in rankings for _ in races],
        RACE: races * len(rankings),
        POSITION: [rank for ranks in rankings.values() for rank in ranks],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=RACE, columns=DRIVER, values=POSITION, sort=False)
x = np.arange(len(table.index))
x_smooth = np.linspace(x[0], x[-1], 300)
low, high = int(df[POSITION].min()), int(df[POSITION].max())

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, driver in enumerate(table.columns):
    ranks = table[driver].to_numpy()
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]

    # Smooth S-curve between periods, passing through the rank at each one
    seen = np.isfinite(ranks)  # a period without a rank is skipped, never drawn as zero
    span = x_smooth[(x_smooth >= x[seen].min()) & (x_smooth <= x[seen].max())]
    if seen.sum() > 1:
        ax.plot(
            span, CubicSpline(x[seen], ranks[seen])(span), linewidth=2.0, color=color, zorder=3, solid_capstyle="round"
        )
    ax.scatter(x[seen], ranks[seen], s=70, color=color, edgecolors=PAGE_BG, linewidths=0.8, zorder=4)

    # Direct label at the line's last period
    ax.text(
        x[seen].max() + 0.2,
        ranks[seen][-1],
        driver,
        fontsize=8,
        fontweight="bold",
        color=color,
        va="center",
        path_effects=[pe.withStroke(linewidth=2, foreground=PAGE_BG)],
    )

# Rank 1 at the top, whole-number ticks only, room on the right for the labels
ax.set_ylim(high + 0.7, low - 0.7)
ax.set_yticks(range(low, high + 1))
ax.set_xlim(-0.5, len(x) - 1 + 2.2)

# Style
ax.set_title("bump-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=8)
ax.set_xlabel(RACE, fontsize=10, color=INK)
ax.set_ylabel(POSITION, fontsize=10, color=INK)
ax.set_xticks(x, table.index, rotation=30, ha="right")
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, color=INK, linewidth=0.6, zorder=1)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.83, top=0.90, bottom=0.18)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
