"""anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
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

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
YEAR = "Year"  # role: time
BROWSER = "Browser"  # role: category
USERS = "Users (millions)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("usage.csv")
years = np.arange(2010, 2025)
browsers = ["Chrome", "Safari", "Edge", "Firefox", "Other"]
users = {
    "Chrome": [310, 420, 530, 640, 760, 880, 1000, 1110, 1200, 1280, 1340, 1380, 1410, 1430, 1440],
    "Safari": [60, 85, 115, 150, 190, 235, 285, 335, 385, 430, 470, 505, 530, 550, 565],
    "Edge": [10, 12, 15, 18, 22, 27, 33, 40, 50, 62, 90, 130, 150, 160, 165],
    "Firefox": [160, 175, 185, 190, 190, 185, 175, 160, 140, 120, 100, 85, 72, 62, 55],
    "Other": [260, 250, 235, 215, 190, 165, 140, 115, 95, 80, 70, 60, 55, 50, 45],
}
df = pd.DataFrame(
    {
        YEAR: np.tile(years, len(browsers)),
        BROWSER: np.repeat(browsers, len(years)),
        USERS: np.concatenate([users[b] for b in browsers]),
    }
)

# Plot: reads only df and the constants above
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
    },
)

order = list(dict.fromkeys(df[BROWSER]))
n_cat = len(order)
palette = dict(zip(order, IMPRINT_PALETTE[:n_cat], strict=True))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

# seaborn's weighted histogram with multiple="fill" normalizes every year to 100 %
sns.histplot(
    data=df,
    x=YEAR,
    hue=BROWSER,
    weights=USERS,
    hue_order=order[::-1],
    multiple="fill",
    discrete=True,
    element="poly",
    palette=palette,
    alpha=0.9,
    linewidth=0.8,
    edgecolor=PAGE_BG,
    legend=True,
    ax=ax,
)

ax.set_title("area-stacked-percent · python · seaborn · anyplot.ai", fontsize=12, color=INK)
ax.set_xlabel(YEAR, fontsize=10)
ax.set_ylabel("Share of users (%)", fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.set_xlim(df[YEAR].min(), df[YEAR].max())
ax.set_ylim(0, 1)
ax.set_yticks(np.linspace(0, 1, 6), [f"{int(v * 100)}" for v in np.linspace(0, 1, 6)])
ax.set_xticks(np.arange(df[YEAR].min(), df[YEAR].max() + 1, 2))
ax.yaxis.grid(True, linewidth=0.6)
ax.set_axisbelow(True)
sns.despine(ax=ax)

sns.move_legend(
    ax,
    "center left",
    bbox_to_anchor=(1.01, 0.5),
    title=BROWSER,
    fontsize=8,
    title_fontsize=9,
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)

fig.subplots_adjust(left=0.08, right=0.87, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
