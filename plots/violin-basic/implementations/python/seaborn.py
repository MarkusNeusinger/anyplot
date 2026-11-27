"""anyplot.ai
violin-basic: Basic Violin Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
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

# Imprint palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns
REGION = "Region"  # role: category
TEMPERATURE = "Temperature (°C)"  # role: value

# Data — daily temperature readings (°C) across four climate regions
np.random.seed(42)
north = np.random.normal(8, 4, 200)  # cold region: compact distribution
south = np.random.normal(24, 6, 200)  # warm region: broader spread
east = np.concatenate([np.random.normal(4, 3, 100), np.random.normal(28, 4, 100)])  # continental: bimodal
west = np.concatenate([np.random.normal(16, 3, 160), np.random.normal(26, 2, 40)])  # coastal: mild, heat events
df = pd.DataFrame(
    {
        REGION: np.repeat(["North", "South", "East", "West"], [len(north), len(south), len(east), len(west)]),
        TEMPERATURE: np.concatenate([north, south, east, west]),
    }
)

# Plot
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

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

n_regions = df[REGION].nunique()
sns.violinplot(
    data=df,
    x=REGION,
    y=TEMPERATURE,
    hue=REGION,
    palette=IMPRINT_PALETTE[:n_regions],
    inner="box",
    cut=0,
    linewidth=1.2,
    saturation=1.0,
    legend=False,
    ax=ax,
)

# Style
ax.set_xlabel(REGION, fontsize=10, color=INK)
ax.set_ylabel(TEMPERATURE, fontsize=10, color=INK)
ax.set_title("violin-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
sns.despine(ax=ax)
ax.yaxis.grid(True, linewidth=0.8)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
