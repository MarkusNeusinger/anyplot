""" pyplots.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import mplcursors
import numpy as np


# Data - Portfolio allocation with asset classes
np.random.seed(42)

# Main asset categories with sub-holdings
categories = {
    "Equities": {"US Large Cap": 25.0, "International": 15.0, "Emerging Markets": 8.0},
    "Fixed Income": {"Government Bonds": 18.0, "Corporate Bonds": 12.0},
    "Alternatives": {"Real Estate": 10.0, "Commodities": 7.0},
    "Cash": {"Money Market": 5.0},
}

# Flatten for outer ring (individual holdings)
holdings = []
weights = []
category_colors = []
category_for_holding = []

# Color scheme by asset class (colorblind-safe)
color_map = {
    "Equities": ["#306998", "#4A8BC2", "#6AA7D6"],  # Blues
    "Fixed Income": ["#2E8B57", "#3CB371"],  # Greens
    "Alternatives": ["#CD853F", "#D2691E"],  # Browns/oranges
    "Cash": ["#708090"],  # Gray
}

for category, assets in categories.items():
    for asset, weight in assets.items():
        holdings.append(asset)
        weights.append(weight)
        colors = color_map[category]
        idx = list(assets.keys()).index(asset)
        category_colors.append(colors[idx % len(colors)])
        category_for_holding.append(category)

# Category totals for inner ring
category_totals = {cat: sum(assets.values()) for cat, assets in categories.items()}
cat_labels = list(category_totals.keys())
cat_weights = list(category_totals.values())
cat_colors = ["#306998", "#2E8B57", "#CD853F", "#708090"]

# Create plot - square format for pie chart
fig, ax = plt.subplots(figsize=(12, 12))

# Outer ring - individual holdings
outer_wedges, outer_texts, outer_autotexts = ax.pie(
    weights,
    labels=None,
    colors=category_colors,
    autopct=lambda pct: f"{pct:.0f}%" if pct >= 8 else "",
    pctdistance=0.82,
    startangle=90,
    radius=1.0,
    wedgeprops={"linewidth": 2, "edgecolor": "white", "width": 0.35},
    textprops={"fontsize": 13, "fontweight": "bold", "color": "white"},
)

# Inner ring - asset categories
inner_wedges, inner_texts, inner_autotexts = ax.pie(
    cat_weights,
    labels=None,
    colors=cat_colors,
    autopct=lambda pct: f"{pct:.0f}%",
    pctdistance=0.72,
    startangle=90,
    radius=0.65,
    wedgeprops={"linewidth": 2, "edgecolor": "white", "width": 0.35},
    textprops={"fontsize": 14, "fontweight": "bold", "color": "white"},
)

# Add center text
ax.text(0, 0, "Portfolio\nAllocation", ha="center", va="center", fontsize=20, fontweight="bold")

# Interactive hover tooltips for outer ring (individual holdings)
cursor_outer = mplcursors.cursor(outer_wedges, hover=True)


@cursor_outer.connect("add")
def on_add_outer(sel):
    idx = outer_wedges.index(sel.artist)
    holding = holdings[idx]
    weight = weights[idx]
    category = category_for_holding[idx]
    sel.annotation.set_text(f"{holding}\n{weight:.1f}%\n({category})")
    sel.annotation.get_bbox_patch().set(fc="white", alpha=0.95)
    sel.annotation.set_fontsize(14)


# Interactive hover tooltips for inner ring (categories)
cursor_inner = mplcursors.cursor(inner_wedges, hover=True)


@cursor_inner.connect("add")
def on_add_inner(sel):
    idx = inner_wedges.index(sel.artist)
    cat = cat_labels[idx]
    weight = cat_weights[idx]
    # List sub-holdings
    sub_holdings = list(categories[cat].keys())
    sub_text = "\n".join([f"  • {h}: {categories[cat][h]:.0f}%" for h in sub_holdings])
    sel.annotation.set_text(f"{cat}: {weight:.0f}%\n{sub_text}")
    sel.annotation.get_bbox_patch().set(fc="white", alpha=0.95)
    sel.annotation.set_fontsize(13)


# Create comprehensive legend showing all holdings grouped by category
legend_handles = []
legend_labels = []

for i, (cat, cat_color) in enumerate(zip(cat_labels, cat_colors, strict=True)):
    # Category header
    legend_handles.append(plt.Rectangle((0, 0), 1, 1, facecolor=cat_color, edgecolor="white", linewidth=1.5))
    legend_labels.append(f"{cat} ({cat_weights[i]:.0f}%)")
    # Individual holdings under this category
    for j, (holding, weight) in enumerate(zip(holdings, weights, strict=True)):
        if category_for_holding[j] == cat:
            legend_handles.append(
                plt.Rectangle((0, 0), 1, 1, facecolor=category_colors[holdings.index(holding)], edgecolor="none")
            )
            legend_labels.append(f"    {holding}: {weight:.0f}%")

ax.legend(
    legend_handles,
    legend_labels,
    loc="center left",
    bbox_to_anchor=(1.05, 0.5),
    fontsize=12,
    frameon=True,
    fancybox=True,
    shadow=False,
    title="Holdings",
    title_fontsize=14,
)

ax.set_title("pie-portfolio-interactive · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
