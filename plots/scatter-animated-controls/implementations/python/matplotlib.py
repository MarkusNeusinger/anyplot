""" anyplot.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Created: 2026-05-15
"""

import os

import matplotlib.pyplot as plt
import numpy as np


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"
ACCENT = "#C475FD"

np.random.seed(42)
countries = 15
years = 25
years_data = np.arange(2000, 2025)

gdp_per_capita = np.zeros((countries, years))
life_expectancy = np.zeros((countries, years))
population = np.zeros((countries, years))
regions = np.random.choice(["Region A", "Region B", "Region C"], countries)

for i in range(countries):
    gdp_per_capita[i, 0] = np.random.uniform(5000, 45000)
    life_expectancy[i, 0] = np.random.uniform(60, 82)
    population[i, 0] = np.random.uniform(10, 300)

    for j in range(1, years):
        gdp_per_capita[i, j] = gdp_per_capita[i, j - 1] * np.random.uniform(1.02, 1.08)
        life_expectancy[i, j] = life_expectancy[i, j - 1] + np.random.uniform(-0.5, 1.0)
        population[i, j] = population[i, j - 1] * np.random.uniform(0.98, 1.03)

key_years_indices = [0, 6, 12, 18, 24]
key_years = years_data[key_years_indices]

colors = [BRAND if region == "Region A" else ACCENT for region in regions]

fig, axes = plt.subplots(1, 5, figsize=(20, 4), facecolor=PAGE_BG)
fig.patch.set_facecolor(PAGE_BG)

for ax_idx, (year_idx, year) in enumerate(zip(key_years_indices, key_years, strict=True)):
    ax = axes[ax_idx]
    ax.set_facecolor(PAGE_BG)

    x = gdp_per_capita[:, year_idx]
    y = life_expectancy[:, year_idx]
    sizes = population[:, year_idx] * 50

    ax.scatter(x, y, s=sizes, c=colors, alpha=0.6, edgecolors=PAGE_BG, linewidth=1)

    ax.set_xlabel("GDP per Capita ($)", fontsize=14, color=INK)
    ax.set_ylabel("Life Expectancy (years)", fontsize=14, color=INK)
    ax.set_title(str(year), fontsize=16, fontweight="medium", color=INK)

    ax.tick_params(axis="both", labelsize=12, colors=INK_SOFT)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(INK_SOFT)
    ax.spines["bottom"].set_color(INK_SOFT)
    ax.yaxis.grid(True, alpha=0.1, linewidth=0.8, color=INK)

    ax.set_xlim(0, 50000)
    ax.set_ylim(55, 85)

fig.suptitle("scatter-animated-controls · matplotlib · anyplot.ai", fontsize=18, fontweight="medium", color=INK, y=1.02)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
