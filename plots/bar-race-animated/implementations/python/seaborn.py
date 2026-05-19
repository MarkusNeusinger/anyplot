""" anyplot.ai
bar-race-animated: Animated Bar Chart Race
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 74/100 | Created: 2026-05-19
"""

import os
import sys


sys.path.pop(0)

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9"]

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

# Data — synthetic tech company market cap ($ billions), 2014–2024
companies = ["Alpha Corp", "Beta Tech", "Gamma Systems", "Delta Networks", "Epsilon Data", "Zeta Cloud"]
years = [2014, 2016, 2018, 2020, 2022, 2024]

market_cap_data = {
    "Alpha Corp": [520, 580, 650, 720, 800, 950],
    "Beta Tech": [380, 450, 560, 680, 810, 1100],
    "Gamma Systems": [290, 340, 410, 500, 620, 750],
    "Delta Networks": [210, 280, 390, 550, 700, 880],
    "Epsilon Data": [160, 220, 310, 430, 580, 670],
    "Zeta Cloud": [120, 180, 290, 420, 560, 780],
}

color_map = {company: OKABE_ITO[i] for i, company in enumerate(companies)}

rows = [
    {"company": company, "year": year, "market_cap": value}
    for company, values in market_cap_data.items()
    for year, value in zip(years, values, strict=True)
]
df = pd.DataFrame(rows)

# Plot — 2×3 small multiples grid of key ranking snapshots
fig, axes = plt.subplots(2, 3, figsize=(16, 9), facecolor=PAGE_BG)
axes = axes.flatten()

for idx, year in enumerate(years):
    ax = axes[idx]
    ax.set_facecolor(PAGE_BG)
    year_data = df[df["year"] == year].sort_values("market_cap", ascending=True)

    colors = [color_map[c] for c in year_data["company"]]
    bars = ax.barh(
        year_data["company"], year_data["market_cap"], color=colors, height=0.65, edgecolor=PAGE_BG, linewidth=0.5
    )

    for bar, val in zip(bars, year_data["market_cap"], strict=True):
        ax.text(
            bar.get_width() + 12,
            bar.get_y() + bar.get_height() / 2,
            f"${val}B",
            va="center",
            ha="left",
            fontsize=10,
            color=INK_SOFT,
        )

    ax.set_title(str(year), fontsize=20, fontweight="bold", color=INK, pad=6)
    ax.tick_params(axis="x", labelsize=11, colors=INK_SOFT)
    ax.tick_params(axis="y", labelsize=12, colors=INK_SOFT)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(INK_SOFT)
    ax.spines["bottom"].set_color(INK_SOFT)

    max_val = year_data["market_cap"].max()
    ax.set_xlim(0, max_val * 1.24)
    ax.xaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
    ax.set_xlabel("Market Cap ($ Billion)", fontsize=12, color=INK_SOFT)

fig.suptitle(
    "Tech Company Rankings · bar-race-animated · python · seaborn · anyplot.ai",
    fontsize=20,
    fontweight="medium",
    color=INK,
    y=0.99,
)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
