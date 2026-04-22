""" pyplots.ai
bubble-basic: Basic Bubble Chart
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-15
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data — World cities: GDP per capita vs life expectancy, bubble = population
np.random.seed(42)
n_cities = 40

gdp_per_capita = np.linspace(5, 85, n_cities) + np.random.normal(0, 5, n_cities)
gdp_per_capita = np.clip(gdp_per_capita, 5, 90)

life_expectancy = 60 + 0.22 * gdp_per_capita + np.random.normal(0, 2.5, n_cities)
life_expectancy = np.clip(life_expectancy, 58, 84)

population_millions = np.random.lognormal(mean=1.0, sigma=1.0, size=n_cities)
population_millions = np.clip(population_millions, 0.8, 30)

# Assign regions based on GDP tiers for color grouping (4th dimension)
region = np.where(
    gdp_per_capita < 25,
    "Emerging",
    np.where(gdp_per_capita < 50, "Developing", np.where(gdp_per_capita < 70, "Advanced", "Elite")),
)

df = pd.DataFrame(
    {
        "GDP per Capita ($ thousands)": np.round(gdp_per_capita, 1),
        "Life Expectancy (years)": np.round(life_expectancy, 1),
        "Population (M)": np.round(population_millions, 1),
        "Economic Tier": region,
    }
)

# Palette — Python Blue anchored, colorblind-safe progression
palette = {"Emerging": "#c44e52", "Developing": "#dd8452", "Advanced": "#55a868", "Elite": "#306998"}

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.scatterplot(
    data=df,
    x="GDP per Capita ($ thousands)",
    y="Life Expectancy (years)",
    size="Population (M)",
    hue="Economic Tier",
    hue_order=["Emerging", "Developing", "Advanced", "Elite"],
    sizes=(150, 2200),
    alpha=0.65,
    palette=palette,
    edgecolor="white",
    linewidth=1.0,
    legend="brief",
    ax=ax,
)

# Style
ax.set_xlabel("GDP per Capita ($ thousands)", fontsize=20)
ax.set_ylabel("Life Expectancy (years)", fontsize=20)
ax.set_title("bubble-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.xaxis.grid(True, alpha=0.08, linewidth=0.5)

# Refine legend — place in lower-right to avoid data overlap
legend = ax.get_legend()
legend.set_title("Economic Tier / Population (M)", prop={"size": 14})
legend.get_title().set_fontweight("semibold")
for text in legend.get_texts():
    text.set_fontsize(13)
legend.set_frame_on(True)
legend.get_frame().set_alpha(0.92)
legend.get_frame().set_edgecolor("#cccccc")
legend.get_frame().set_facecolor("white")
sns.move_legend(ax, "lower right", frameon=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
