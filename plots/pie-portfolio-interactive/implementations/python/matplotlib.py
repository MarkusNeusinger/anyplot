""" anyplot.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-27
"""

import os

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
PCT_COLOR = "#FFFDF6" if THEME == "light" else "#F0EFE8"

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — diversified balanced fund allocation
PORTFOLIO_TOTAL = 1_000_000

categories = {
    "Equities": {"US Large Cap": 25.0, "International": 15.0, "Emerging Markets": 8.0},
    "Fixed Income": {"Government Bonds": 18.0, "Corporate Bonds": 12.0},
    "Alternatives": {"Real Estate": 10.0, "Commodities": 7.0},
    "Cash": {"Money Market": 5.0},
}

cat_labels = list(categories.keys())
cat_weights = [sum(assets.values()) for assets in categories.values()]
cat_colors = ANYPLOT_PALETTE[:4]

holdings = []
holding_weights = []
holding_cat_idx = []

for i, (_cat, assets) in enumerate(categories.items()):
    for asset, weight in assets.items():
        holdings.append(asset)
        holding_weights.append(weight)
        holding_cat_idx.append(i)

holding_colors = [cat_colors[i] for i in holding_cat_idx]

# Plot — square canvas for pie/donut chart
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
fig.subplots_adjust(left=0.0, right=0.52, top=0.92, bottom=0.02)

# Inner ring — asset class totals
inner_wedges, _, inner_pcts = ax.pie(
    cat_weights,
    labels=None,
    colors=cat_colors,
    autopct=lambda pct: f"{pct:.0f}%",
    pctdistance=0.70,
    startangle=90,
    radius=0.56,
    wedgeprops={"linewidth": 2.0, "edgecolor": PAGE_BG, "width": 0.32},
    textprops={"fontsize": 8, "fontweight": "bold"},
)
for txt in inner_pcts:
    txt.set_color(PCT_COLOR)

# Outer ring — individual holdings (slightly transparent to suggest sub-level)
outer_wedges, _, outer_pcts = ax.pie(
    holding_weights,
    labels=None,
    colors=holding_colors,
    autopct=lambda pct: f"{pct:.0f}%" if pct >= 8 else "",
    pctdistance=0.84,
    startangle=90,
    radius=1.0,
    wedgeprops={"linewidth": 1.5, "edgecolor": PAGE_BG, "width": 0.44},
    textprops={"fontsize": 7},
)
for wedge in outer_wedges:
    wedge.set_alpha(0.72)
for txt in outer_pcts:
    txt.set_color(PCT_COLOR)

# Center label
ax.text(0, 0, "Portfolio\nAllocation", ha="center", va="center", fontsize=10, fontweight="bold", color=INK)

# Legend — categories with indented sub-holdings
legend_handles = []
legend_labels = []
for i, cat in enumerate(cat_labels):
    legend_handles.append(Patch(facecolor=cat_colors[i], edgecolor=INK_MUTED, linewidth=0.8))
    cat_value = cat_weights[i] / 100 * PORTFOLIO_TOTAL
    legend_labels.append(f"{cat}  {cat_weights[i]:.0f}%  ${cat_value:,.0f}")
    for j in range(len(holdings)):
        if holding_cat_idx[j] == i:
            legend_handles.append(Patch(facecolor=cat_colors[i], alpha=0.60, edgecolor=INK_MUTED, linewidth=0.5))
            holding_value = holding_weights[j] / 100 * PORTFOLIO_TOTAL
            legend_labels.append(f"  {holdings[j]}  {holding_weights[j]:.0f}%  ${holding_value:,.0f}")

leg = ax.legend(
    legend_handles,
    legend_labels,
    loc="center left",
    bbox_to_anchor=(1.06, 0.5),
    fontsize=8,
    frameon=True,
    title="Asset Allocation",
    title_fontsize=8,
    borderpad=1.0,
    labelspacing=0.55,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

# Title — centered on full figure width (not just the pie axes) to prevent clipping
title = "pie-portfolio-interactive · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
fig.text(0.50, 0.96, title, ha="center", va="top", fontsize=title_fontsize, fontweight="medium", color=INK)

fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
