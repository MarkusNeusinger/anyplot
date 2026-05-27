"""anyplot.ai
pie-portfolio-interactive: Portfolio Allocation Chart
Library: seaborn 0.13.2 | Python 3.13
Quality: 91/100 | Updated: 2026-05-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# anyplot palette — semantic: green=equities (growth), blue=fixed income (stability), ochre=alternatives
CATEGORY_BASES = {"Equities": "#009E73", "Fixed Income": "#4467A3", "Alternatives": "#BD8233"}

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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data — diversified investment portfolio
portfolio_data = pd.DataFrame(
    {
        "asset": [
            "US Large Cap Equity",
            "International Equity",
            "Emerging Markets",
            "US Treasury Bonds",
            "Corporate Bonds",
            "Municipal Bonds",
            "REITs",
            "Gold",
            "Private Equity",
        ],
        "weight": [28.0, 15.0, 7.0, 18.0, 12.0, 5.0, 6.0, 4.0, 5.0],
        "category": [
            "Equities",
            "Equities",
            "Equities",
            "Fixed Income",
            "Fixed Income",
            "Fixed Income",
            "Alternatives",
            "Alternatives",
            "Alternatives",
        ],
        "value": [280000, 150000, 70000, 180000, 120000, 50000, 60000, 40000, 50000],
    }
)

category_data = portfolio_data.groupby("category").agg({"weight": "sum", "value": "sum"}).reset_index()

# Build per-category color gradients using seaborn palette tools and anyplot base colors
category_rgb = {cat: sns.color_palette([hex_c])[0] for cat, hex_c in CATEGORY_BASES.items()}

asset_colors = []
for _, row in portfolio_data.iterrows():
    base_rgb = category_rgb[row["category"]]
    cat_mask = portfolio_data["category"] == row["category"]
    cat_assets = portfolio_data[cat_mask]
    pos = list(cat_assets.index).index(cat_assets[cat_assets["asset"] == row["asset"]].index[0])
    n = len(cat_assets)
    light = sns.light_palette(base_rgb, n_colors=n + 2)[1]
    dark = sns.dark_palette(base_rgb, n_colors=n + 2, reverse=True)[1]
    blend = sns.blend_palette([light, base_rgb, dark], n_colors=n + 2)
    asset_colors.append(blend[pos + 1])

# Canvas — square for symmetric donut chart
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Outer ring — individual holdings breakdown
outer_wedges, _, outer_autotexts = ax.pie(
    portfolio_data["weight"],
    labels=None,
    colors=asset_colors,
    autopct=lambda pct: f"{pct:.1f}%" if pct > 5 else "",
    startangle=90,
    radius=1.0,
    pctdistance=0.82,
    wedgeprops={"width": 0.35, "edgecolor": PAGE_BG, "linewidth": 1.5},
)
for autotext in outer_autotexts:
    autotext.set_fontsize(8)
    autotext.set_fontweight("bold")
    autotext.set_color(INK)

# Inner ring — asset class aggregates
inner_colors = [category_rgb[cat] for cat in category_data["category"]]
inner_wedges, _, inner_autotexts = ax.pie(
    category_data["weight"],
    labels=None,
    colors=inner_colors,
    autopct=lambda pct: f"{pct:.0f}%",
    startangle=90,
    radius=0.65,
    pctdistance=0.5,
    wedgeprops={"width": 0.35, "edgecolor": PAGE_BG, "linewidth": 1.5},
)
for autotext in inner_autotexts:
    autotext.set_fontsize(9)
    autotext.set_fontweight("bold")
    autotext.set_color("#FFFFFF")

# Center label — total portfolio value
total_value = portfolio_data["value"].sum()
ax.text(
    0,
    0,
    f"Portfolio\n${total_value / 1_000_000:.1f}M",
    ha="center",
    va="center",
    fontsize=10,
    fontweight="bold",
    color=INK,
)

# Data labels for the four largest holdings
cumulative = 0.0
angle_mid = {}
for _, row in portfolio_data.iterrows():
    angle_mid[row["asset"]] = 90 - cumulative - row["weight"] / 2
    cumulative += row["weight"]

for _, row in portfolio_data.nlargest(4, "weight").iterrows():
    theta = np.deg2rad(angle_mid[row["asset"]])
    r_text = 1.26
    x_t, y_t = r_text * np.cos(theta), r_text * np.sin(theta)
    ha = "left" if x_t > 0.15 else ("right" if x_t < -0.15 else "center")
    dx = 0.04 if x_t > 0.15 else (-0.04 if x_t < -0.15 else 0)

    ax.annotate(
        f"{row['asset']}\n${row['value']:,.0f}  ({row['weight']:.0f}%)",
        xy=(0.97 * np.cos(theta), 0.97 * np.sin(theta)),
        xytext=(x_t + dx, y_t),
        fontsize=6,
        ha=ha,
        va="center",
        color=INK,
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": ELEVATED_BG,
            "edgecolor": CATEGORY_BASES[row["category"]],
            "linewidth": 1.5,
            "alpha": 0.92,
        },
        arrowprops={"arrowstyle": "-", "color": INK_MUTED, "connectionstyle": "arc3,rad=0.1", "linewidth": 0.8},
    )

# Legend — asset class breakdown summary
legend_labels = [
    f"{r['category']}: {r['weight']:.0f}%  (${r['value'] / 1000:.0f}K, "
    f"{len(portfolio_data[portfolio_data['category'] == r['category']])} holdings)"
    for _, r in category_data.iterrows()
]
legend = ax.legend(
    inner_wedges,
    legend_labels,
    title="Asset Classes",
    loc="lower center",
    bbox_to_anchor=(0.5, -0.05),
    fontsize=6,
    title_fontsize=7,
    frameon=True,
    fancybox=True,
    ncol=3,
    columnspacing=0.8,
)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
legend.get_title().set_color(INK)
for text in legend.get_texts():
    text.set_color(INK_SOFT)

# Title and layout
title = "pie-portfolio-interactive · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=14)
ax.set_aspect("equal")
ax.set_xlim(-1.65, 1.65)
ax.set_ylim(-1.35, 1.35)

fig.subplots_adjust(bottom=0.13)

# Save — no bbox_inches="tight" to preserve exact 2400×2400 canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
