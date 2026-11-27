"""anyplot.ai
box-basic: Basic Box Plot
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-27
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

# Imprint palette, canonical order
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
    },
)

# Columns
ZONE = "City Zone"  # role: category
PM25 = "PM2.5 (ug/m3)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("pm25.csv")
# Daily PM2.5 air quality readings (ug/m3) across 5 city zones
np.random.seed(42)

zones_config = [
    ("Park", "normal", 8, 3, 90),
    ("Residential", "normal", 18, 5, 80),
    ("Commercial", "normal", 30, 6, 75),
    ("Downtown", "bimodal", None, None, 100),
    ("Industrial", "exponential", None, 14, 70),
]

records = []
for zone, dist, loc, scale, n in zones_config:
    if dist == "bimodal":
        values = np.concatenate([np.random.normal(25, 5, n // 2), np.random.normal(44, 6, n // 2)])
    elif dist == "exponential":
        values = np.random.exponential(scale, n) + 28
    else:
        values = np.random.normal(loc, scale, n)
    values = np.clip(values, 1, None)
    for v in values:
        records.append({ZONE: zone, PM25: v})

df = pd.DataFrame(records)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
zones = list(df[ZONE].unique())
palette = [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(len(zones))]

sns.boxplot(
    data=df,
    x=ZONE,
    y=PM25,
    hue=ZONE,
    order=zones,
    hue_order=zones,
    palette=palette,
    saturation=1,
    linewidth=1.5,
    linecolor=INK_SOFT,
    width=0.55,
    medianprops={"color": INK, "linewidth": 2.5},
    flierprops={"marker": "o", "markersize": 4, "markerfacecolor": "none", "markeredgecolor": INK_SOFT},
    legend=False,
    ax=ax,
)

# Style
ax.set_title("box-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(ZONE, fontsize=10, color=INK)
ax.set_ylabel(PM25, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
sns.despine(ax=ax)

plt.tight_layout()

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
