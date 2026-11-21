"""anyplot.ai
line-stepwise: Step Line Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-13
"""

import os

import matplotlib.pyplot as plt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is always brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: x
CAPACITY = "Server capacity (units)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("capacity.csv")
df = pd.DataFrame(
    {
        HOUR: list(range(24)),
        CAPACITY: [50, 50, 50, 50, 50, 50, 75, 75, 100, 100, 100, 100]
        + [150, 150, 150, 125, 125, 100, 100, 75, 75, 75, 50, 50],
    }
)

# Plot: reads only df and the constants above
title = "line-stepwise · python · matplotlib · anyplot.ai"
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# 'post' alignment: each value is held until the next data point
ax.step(df[HOUR], df[CAPACITY], where="post", linewidth=2.5, color=IMPRINT_PALETTE[0])
ax.fill_between(df[HOUR], df[CAPACITY], step="post", alpha=0.15, color=IMPRINT_PALETTE[0])
ax.scatter(df[HOUR], df[CAPACITY], s=28, color=IMPRINT_PALETTE[0], edgecolors=PAGE_BG, linewidths=0.8, zorder=5)

# Style
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(HOUR, fontsize=10, color=INK)
ax.set_ylabel(CAPACITY, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

ax.set_xlim(df[HOUR].min() - 0.5, df[HOUR].max() + 0.5)
ax.set_ylim(0, df[CAPACITY].max() * 1.17)
ticks = df[HOUR].dropna().iloc[::2].astype(float)
ax.set_xticks(ticks, [f"{h:02.0f}:00" for h in ticks])

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK_SOFT)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
