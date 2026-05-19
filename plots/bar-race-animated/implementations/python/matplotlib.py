"""anyplot.ai
bar-race-animated: Animated Bar Chart Race
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-05-19
"""

import os

import matplotlib.pyplot as plt


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data: Tech Company Market Cap ($B) — year-end snapshots (2019–2024)
companies = ["Alphabet", "Amazon", "Apple", "Meta", "Microsoft", "Nvidia", "Tesla"]
company_colors = {c: OKABE_ITO[i] for i, c in enumerate(companies)}

market_cap = {
    "Alphabet": [920, 1200, 1960, 1140, 1800, 2150],
    "Amazon": [940, 1640, 1730, 855, 1570, 2170],
    "Apple": [1050, 2250, 2950, 2070, 2990, 3750],
    "Meta": [580, 780, 890, 335, 940, 1440],
    "Microsoft": [1200, 1680, 2530, 1790, 2800, 3130],
    "Nvidia": [145, 325, 745, 365, 1220, 3280],
    "Tesla": [75, 670, 1060, 388, 790, 695],
}
years = [2019, 2020, 2021, 2022, 2023, 2024]

max_val = max(v for vlist in market_cap.values() for v in vlist)

# Plot: 2×3 small multiples — key snapshots from the bar chart race
fig, axes = plt.subplots(2, 3, figsize=(16, 9), facecolor=PAGE_BG)
axes = axes.flatten()

for idx, (year, ax) in enumerate(zip(years, axes, strict=False)):
    ax.set_facecolor(PAGE_BG)

    # Sort ascending so the highest-value company tops the chart
    snapshot = {c: market_cap[c][idx] for c in companies}
    sorted_items = sorted(snapshot.items(), key=lambda x: x[1])
    names = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]
    bar_colors = [company_colors[n] for n in names]

    ax.barh(names, values, color=bar_colors, height=0.72, edgecolor=PAGE_BG, linewidth=0.8)

    # Value labels on right side of each bar
    offset = max_val * 0.02
    for i, (_name, val) in enumerate(zip(names, values, strict=False)):
        ax.text(val + offset, i, f"${val:,}B", va="center", ha="left", fontsize=9, color=INK_SOFT)

    ax.set_title(str(year), fontsize=14, fontweight="bold", color=INK, pad=5)
    ax.set_xlim(0, max_val * 1.35)
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=9.5, colors=INK_SOFT, length=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_color(INK_SOFT)

fig.suptitle(
    "Tech Giant Market Cap · bar-race-animated · python · matplotlib · anyplot.ai",
    fontsize=20,
    fontweight="medium",
    color=INK,
)

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
