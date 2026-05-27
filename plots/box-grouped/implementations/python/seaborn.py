""" anyplot.ai
box-grouped: Grouped Box Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-08
"""

import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Temperature distributions by region and season
np.random.seed(42)

regions = ["North", "South", "East", "West"]
seasons = ["Winter", "Spring", "Summer", "Fall"]

data = []
for region in regions:
    for season in seasons:
        n = np.random.randint(35, 50)
        # Different temperature distributions per region/season
        season_base = {"Winter": 5, "Spring": 15, "Summer": 28, "Fall": 18}[season]
        region_offset = {"North": -3, "South": 2, "East": 0, "West": 1}[region]
        base = season_base + region_offset

        season_spread = {"Winter": 4, "Spring": 5, "Summer": 6, "Fall": 5}[season]
        values = np.random.normal(base, season_spread, n)
        # Add realistic outliers (unusual temperature days)
        if np.random.random() > 0.6:
            values = np.append(
                values, base + season_spread * np.random.choice([-2.5, 2.5], size=1)
            )
        values = np.clip(values, -10, 40)

        for v in values:
            data.append({"Region": region, "Season": season, "Temperature (°C)": v})

df = pd.DataFrame(data)

# Plot setup
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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(16, 9))

# Create grouped box plot
sns.boxplot(
    data=df,
    x="Region",
    y="Temperature (°C)",
    hue="Season",
    palette=IMPRINT,
    ax=ax,
    width=0.7,
    linewidth=2,
    fliersize=8,
    order=regions,
    hue_order=seasons,
)

# Styling
ax.set_xlabel("Region", fontsize=20, color=INK)
ax.set_ylabel("Temperature (°C)", fontsize=20, color=INK)
ax.set_title("box-grouped · seaborn · anyplot.ai", fontsize=24, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.legend(title="Season", fontsize=14, title_fontsize=16, loc="upper right")
ax.set_ylim(-12, 42)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.xaxis.grid(False)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
