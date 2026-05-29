""" anyplot.ai
violin-basic: Basic Violin Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-29
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
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data — daily temperature readings (°C) across four climate regions
np.random.seed(42)
regions = ["North", "South", "East", "West"]
records = []

for region in regions:
    if region == "North":
        # Cold region: compact distribution
        temps = np.random.normal(8, 4, 200)
    elif region == "South":
        # Warm region: broader spread
        temps = np.random.normal(24, 6, 200)
    elif region == "East":
        # Continental: bimodal (cold winters + hot summers) — showcases KDE strength
        temps = np.concatenate([np.random.normal(4, 3, 100), np.random.normal(28, 4, 100)])
    else:
        # Coastal: mild with occasional heat events
        temps = np.concatenate([np.random.normal(16, 3, 160), np.random.normal(26, 2, 40)])
    for t in temps:
        records.append({"Region": region, "Temperature (°C)": t})

df = pd.DataFrame(records)

# Canvas — 3200 × 1800 px (landscape 16:9)
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
ax.set_facecolor(PAGE_BG)

# Violin plot
sns.violinplot(
    data=df,
    x="Region",
    y="Temperature (°C)",
    hue="Region",
    palette=IMPRINT_PALETTE,
    inner="box",
    cut=0,
    linewidth=1.2,
    saturation=1.0,
    legend=False,
    ax=ax,
)

# Stripplot overlay — signature seaborn layering pattern
sns.stripplot(
    data=df,
    x="Region",
    y="Temperature (°C)",
    hue="Region",
    palette=IMPRINT_PALETTE,
    dodge=False,
    jitter=0.2,
    size=1.5,
    alpha=0.2,
    legend=False,
    ax=ax,
)

# Style
title = "violin-basic · python · seaborn · anyplot.ai"
ax.set_xlabel("Region", fontsize=10, color=INK)
ax.set_ylabel("Temperature (°C)", fontsize=10, color=INK)
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Save — no bbox_inches='tight' (seaborn canvas contract: figsize×dpi sets exact target)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
