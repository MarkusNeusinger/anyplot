"""anyplot.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-05-20
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

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

# Data — regional annual sales with quarterly breakdown
regions = ["North", "South", "East", "West"]
region_totals = [12.4, 8.7, 15.2, 10.1]
quarters = ["Q1", "Q2", "Q3", "Q4"]
quarterly = {
    "North": [2.8, 3.1, 3.4, 3.1],
    "South": [1.9, 2.3, 2.2, 2.3],
    "East": [3.5, 3.9, 4.1, 3.7],
    "West": [2.4, 2.5, 2.7, 2.5],
}

df_top = pd.DataFrame({"Region": regions, "Revenue": region_totals})
df_sub = pd.DataFrame(
    [{"Region": r, "Quarter": q, "Revenue": quarterly[r][i]} for r in regions for i, q in enumerate(quarters)]
)

# Plot
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(8, 4.5), dpi=400, gridspec_kw={"height_ratios": [2, 3]}, facecolor=PAGE_BG
)

# Top panel — overview level (region totals)
sns.barplot(data=df_top, x="Region", y="Revenue", color=BRAND, ax=ax1)
for p in ax1.patches:
    ax1.text(
        p.get_x() + p.get_width() / 2.0,
        p.get_height() + 0.25,
        f"${p.get_height():.1f}M",
        ha="center",
        va="bottom",
        fontsize=8,
        color=INK_SOFT,
    )
ax1.set_title(
    "Sales by Region · bar-drilldown · python · seaborn · anyplot.ai",
    fontsize=10,
    fontweight="medium",
    color=INK,
    pad=8,
)
ax1.set_xlabel("")
ax1.set_ylabel("Annual Revenue ($M)", fontsize=10, color=INK)
ax1.tick_params(axis="both", labelsize=8)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax1.set_facecolor(PAGE_BG)

# Bottom panel — quarterly drill level (breakdown per region)
sns.barplot(data=df_sub, x="Region", y="Revenue", hue="Quarter", palette=OKABE_ITO, ax=ax2)
ax2.set_xlabel("Region", fontsize=10, color=INK)
ax2.set_ylabel("Quarterly Revenue ($M)", fontsize=10, color=INK)
ax2.tick_params(axis="both", labelsize=8)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax2.set_facecolor(PAGE_BG)
leg = ax2.legend(title="Quarter", fontsize=8, title_fontsize=8, loc="upper right", framealpha=0.9)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)

plt.tight_layout(h_pad=3.0)
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
