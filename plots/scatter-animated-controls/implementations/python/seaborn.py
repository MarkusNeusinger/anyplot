""" anyplot.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 81/100 | Created: 2026-05-15
"""

import os
import sys

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Prioritize site-packages to avoid importing local seaborn.py file
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if "site-packages" in p] + [
    p for p in sys.path if "site-packages" not in p and os.path.abspath(p) != _script_dir
]
import seaborn as sns  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1
COLORS = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data: Simulate country-level metrics evolving over time (Gapminder-inspired)
np.random.seed(42)

countries = ["Country A", "Country B", "Country C", "Country D", "Country E"]
years = np.arange(2000, 2021, 5)  # Key time points: 2000, 2005, 2010, 2015, 2020

data_list = []
for country in countries:
    base_gdp = np.random.uniform(5000, 30000)
    base_life = np.random.uniform(65, 78)

    for year in years:
        # GDP per capita grows over time with some randomness
        gdp_per_capita = base_gdp * (1.03 ** (year - 2000)) + np.random.normal(0, 1000)
        # Life expectancy improves over time
        life_expectancy = base_life + (year - 2000) * 0.2 + np.random.normal(0, 0.5)
        # Population proxy (for marker size)
        population = np.random.uniform(20, 100)

        data_list.append(
            {
                "Year": year,
                "Country": country,
                "GDP per Capita ($1000s)": gdp_per_capita / 1000,
                "Life Expectancy (years)": life_expectancy,
                "Population Proxy": population,
            }
        )

df = pd.DataFrame(data_list)

# Create faceted plot showing temporal evolution
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.2)

# Configure theme colors
matplotlib.rcParams.update(
    {
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "grid.linewidth": 0.8,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    }
)

# Use relplot for faceted scatter with automatic data handling
g = sns.relplot(
    data=df,
    x="GDP per Capita ($1000s)",
    y="Life Expectancy (years)",
    hue="Country",
    col="Year",
    col_wrap=3,
    palette=COLORS,
    height=4.3,
    aspect=1.05,
    s=150,
    alpha=0.8,
    edgecolor="face",
    linewidths=0.5,
)

# Set axis labels and limits for consistency
g.set_axis_labels("GDP per Capita ($1000s)", "Life Expectancy (years)", fontsize=14)
for ax in g.axes.flat:
    ax.set_xlim(5, 45)
    ax.set_ylim(64, 82)
    ax.tick_params(labelsize=12, colors=INK_SOFT)
    ax.set_xlabel("GDP per Capita ($1000s)", fontsize=14, color=INK)
    ax.set_ylabel("Life Expectancy (years)", fontsize=14, color=INK)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(INK_SOFT)

# Configure legend
g._legend.set_title("Country")
g._legend.get_frame().set_facecolor(ELEVATED_BG)
g._legend.get_frame().set_edgecolor(INK_SOFT)
g._legend.get_title().set_color(INK)
g._legend.get_title().set_fontsize(13)
for text in g._legend.get_texts():
    text.set_color(INK)
    text.set_fontsize(12)

# Main title
fig = g.figure
fig.suptitle("scatter-animated-controls · seaborn · anyplot.ai", fontsize=20, fontweight="medium", color=INK, y=0.98)
fig.patch.set_facecolor(PAGE_BG)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
plt.close()
