""" anyplot.ai
facet-grid: Faceted Grid Plot
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import linregress


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TEMPERATURE = "Temperature (°C)"  # role: x
ENERGY = "Energy Consumption (kWh)"  # role: y
REGION = "Region"  # role: row_facet
SEASON = "Season"  # role: col_facet

# Data: replace this block with your own table, for example df = pd.read_csv("energy.csv")
np.random.seed(42)
base_temps = {"North": 5, "South": 20, "East": 15}
season_offsets = {"Spring": 5, "Summer": 10, "Fall": 2, "Winter": -8}
rows = []
for region, region_temp in base_temps.items():
    for season, offset in season_offsets.items():
        center = region_temp + offset
        temp = np.random.normal(center, 4, 25)
        # U-shaped energy demand around the panel's typical temperature
        energy = 120 + (temp - center) ** 2 * 0.2 + np.random.normal(0, 8, 25)
        rows.append(pd.DataFrame({TEMPERATURE: temp, ENERGY: energy, REGION: region, SEASON: season}))
df = pd.concat(rows, ignore_index=True)

# Plot: reads only df and the constants above
regions = df[REGION].unique()
seasons = df[SEASON].unique()

fig, axes = plt.subplots(
    len(regions), len(seasons), figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, sharex=True, sharey=True, squeeze=False
)
fig.subplots_adjust(left=0.11, right=0.985, top=0.89, bottom=0.14, hspace=0.18, wspace=0.08)

for i, region in enumerate(regions):
    for j, season in enumerate(seasons):
        ax = axes[i, j]
        ax.set_facecolor(PAGE_BG)
        subset = df[(df[REGION] == region) & (df[SEASON] == season)]

        ax.scatter(
            subset[TEMPERATURE],
            subset[ENERGY],
            s=26,
            alpha=0.75,
            color=IMPRINT_PALETTE[i],
            edgecolors=PAGE_BG,
            linewidth=0.4,
            zorder=3,
        )

        # Linear trend per panel
        if len(subset) > 1:
            fit = linregress(subset[TEMPERATURE], subset[ENERGY])
            x_line = np.array([subset[TEMPERATURE].min(), subset[TEMPERATURE].max()])
            ax.plot(x_line, fit.slope * x_line + fit.intercept, color=INK_MUTED, linewidth=1.3, alpha=0.6, zorder=2)

        ax.yaxis.grid(True, alpha=0.12, linewidth=0.5, color=INK)
        ax.xaxis.grid(True, alpha=0.08, linewidth=0.5, color=INK)
        ax.set_axisbelow(True)

        if i == 0:
            ax.set_title(season, fontsize=10, color=INK, fontweight="semibold", pad=4)
        if j == 0:
            ax.set_ylabel(region, fontsize=10, color=INK, fontweight="semibold")

        ax.tick_params(axis="both", labelsize=7, colors=INK_SOFT, labelcolor=INK_SOFT, length=2.5, width=0.5)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color(INK_SOFT)
            ax.spines[spine].set_linewidth(0.6)

# Shared axis titles for the whole grid
fig.supxlabel(TEMPERATURE, fontsize=10, color=INK, y=0.01)
fig.supylabel(ENERGY, fontsize=10, color=INK, x=0.008)
fig.suptitle("facet-grid · python · matplotlib · anyplot.ai", fontsize=13, fontweight="medium", color=INK, y=0.975)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
