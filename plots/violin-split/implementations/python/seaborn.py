""" anyplot.ai
violin-split: Split Violin Plot
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-16
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

# Imprint palette: canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Library setup
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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
REGION = "Region"  # role: category
ENERGY = "Daily electricity use (kWh per household)"  # role: value
SEASON = "Season"  # role: split_group

# Data: replace this block with your own table, for example df = pd.read_csv("energy.csv")
rng = np.random.default_rng(7)
regions = ["Nordic", "Mediterranean", "Continental", "Atlantic", "Alpine"]
# (mean, spread) per region for summer and winter; Nordic and Alpine winters are bimodal (cold snaps)
params = {
    "Nordic": {"Summer": [(9.0, 1.6)], "Winter": [(17.0, 2.5), (24.0, 2.0)]},
    "Mediterranean": {"Summer": [(17.0, 3.0), (23.0, 2.2)], "Winter": [(11.0, 1.8)]},
    "Continental": {"Summer": [(12.0, 2.0)], "Winter": [(15.0, 3.4)]},
    "Atlantic": {"Summer": [(10.0, 1.4)], "Winter": [(12.5, 1.7)]},
    "Alpine": {"Summer": [(8.5, 1.5)], "Winter": [(14.0, 2.0), (21.0, 2.4)]},
}
rows = []
for region in regions:
    for season, modes in params[region].items():
        n = 220
        pick = rng.integers(0, len(modes), n)
        values = np.array([rng.normal(*modes[k]) for k in pick])
        rows.append(pd.DataFrame({REGION: region, SEASON: season, ENERGY: np.clip(values, 3, None)}))
df = pd.concat(rows, ignore_index=True)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

n_seasons = df[SEASON].nunique()
sns.violinplot(
    data=df,
    x=REGION,
    y=ENERGY,
    hue=SEASON,
    split=True,
    inner="quart",
    cut=0,
    density_norm="width",
    palette=IMPRINT_PALETTE[:n_seasons],
    linewidth=0.9,
    inner_kws={"color": INK, "linewidth": 0.9},
    ax=ax,
)

# Style
title = "violin-split · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=10)
ax.set_xlabel(REGION, fontsize=10, color=INK)
ax.set_ylabel(ENERGY, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.set_ylim(top=df[ENERGY].max() * 1.22)
sns.despine(ax=ax)
ax.yaxis.grid(True, color=INK, alpha=0.10, linewidth=0.6)
ax.set_axisbelow(True)

legend = ax.legend(title=SEASON, fontsize=8, title_fontsize=9, loc="upper right", framealpha=0.95)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
legend.get_title().set_color(INK)
for text in legend.get_texts():
    text.set_color(INK)

fig.tight_layout()
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
