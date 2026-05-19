"""anyplot.ai
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

# Synthetic market cap ($ billions) with sector rotations, corrections, and breakouts
companies = ["Alpha Corp", "Beta Tech", "Gamma Systems", "Delta Networks", "Epsilon Data", "Zeta Cloud"]
years = [2014, 2016, 2018, 2020, 2022, 2024]

market_cap_data = {
    "Alpha Corp": [520, 610, 720, 680, 750, 820],  # correction in 2020
    "Beta Tech": [380, 430, 510, 600, 820, 1100],  # breakout surge to #1 by 2022
    "Gamma Systems": [290, 370, 460, 530, 490, 620],  # peak then dip in 2022
    "Delta Networks": [210, 280, 390, 550, 700, 880],  # consistent riser
    "Epsilon Data": [160, 250, 420, 380, 540, 670],  # volatile: rises, dips, recovers
    "Zeta Cloud": [120, 180, 260, 310, 410, 580],  # steady late-stage grower
}

color_map = {company: OKABE_ITO[i] for i, company in enumerate(companies)}

rows = [
    {"company": company, "year": year, "market_cap": value}
    for company, values in market_cap_data.items()
    for year, value in zip(years, values, strict=True)
]
df = pd.DataFrame(rows)
df["rank"] = df.groupby("year")["market_cap"].rank(ascending=False, method="first").astype(int)

fig, axes = plt.subplots(2, 3, figsize=(16, 9), facecolor=PAGE_BG)
axes = axes.flatten()

prev_rank = None

for idx, year in enumerate(years):
    ax = axes[idx]
    ax.set_facecolor(PAGE_BG)

    year_data = df[df["year"] == year].sort_values("market_cap", ascending=True).reset_index(drop=True)
    order = list(year_data["company"])
    curr_rank = dict(zip(year_data["company"], year_data["rank"], strict=True))

    # Rank change: positive = moved up in ranking
    rank_delta = {}
    if prev_rank is not None:
        for co in companies:
            rank_delta[co] = prev_rank.get(co, 6) - curr_rank.get(co, 6)

    # Use sns.barplot — the idiomatic seaborn horizontal bar function
    sns.barplot(
        data=year_data,
        x="market_cap",
        y="company",
        hue="company",
        palette=color_map,
        order=order,
        dodge=False,
        legend=False,
        ax=ax,
    )

    max_val = year_data["market_cap"].max()
    ax.set_xlim(0, max_val * 1.45)

    # Highlight rank movers: thicker colored edge for companies up ≥2 positions
    bar_patches = sorted([p for p in ax.patches if p.get_width() > 0], key=lambda p: p.get_y())
    for patch, company in zip(bar_patches, order, strict=True):
        delta = rank_delta.get(company, 0)
        if delta >= 2:
            patch.set_edgecolor(color_map[company])
            patch.set_linewidth(2.5)
        else:
            patch.set_edgecolor(PAGE_BG)
            patch.set_linewidth(0.5)

    # Value labels with rank-change badge on movers
    for patch, company in zip(bar_patches, order, strict=True):
        val = year_data.loc[year_data["company"] == company, "market_cap"].values[0]
        delta = rank_delta.get(company, 0)
        badge = f"  ▲{delta}" if delta >= 2 else (f"  ▼{-delta}" if delta <= -2 else "")
        label_color = color_map[company] if abs(delta) >= 2 else INK_SOFT
        ax.text(
            patch.get_width() + max_val * 0.012,
            patch.get_y() + patch.get_height() / 2,
            f"${val}B{badge}",
            va="center",
            ha="left",
            fontsize=14,
            color=label_color,
            fontweight="bold" if abs(delta) >= 2 else "normal",
        )

    ax.set_title(str(year), fontsize=20, fontweight="bold", color=INK, pad=6)
    ax.tick_params(axis="x", labelsize=16, colors=INK_SOFT)
    ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(INK_SOFT)
    ax.spines["bottom"].set_color(INK_SOFT)

    ax.xaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
    ax.set_xlabel("Market Cap ($ Billion)", fontsize=20, color=INK_SOFT)
    ax.set_ylabel("")

    prev_rank = curr_rank

fig.suptitle(
    "Tech Company Rankings · bar-race-animated · python · seaborn · anyplot.ai",
    fontsize=24,
    fontweight="medium",
    color=INK,
    y=0.99,
)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
