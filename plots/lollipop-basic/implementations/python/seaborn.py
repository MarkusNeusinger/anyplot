""" anyplot.ai
lollipop-basic: Basic Lollipop Chart
Library: seaborn 0.13.2 | Python 3.14.4
Quality: 87/100 | Updated: 2026-04-26
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

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

# Data - Product sales by category
categories = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports",
    "Books",
    "Toys",
    "Beauty",
    "Automotive",
    "Food & Grocery",
    "Health",
]
values = [85000, 72000, 58000, 45000, 42000, 38000, 35000, 28000, 25000, 18000]

df = pd.DataFrame({"category": categories, "value": values}).sort_values("value", ascending=True)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Stems: thin lines from baseline to marker
ax.hlines(y=df["category"], xmin=0, xmax=df["value"], color=BRAND, linewidth=2.5, alpha=0.85, zorder=2)

# Markers: circular dots at the data values
sns.scatterplot(
    data=df, x="value", y="category", s=450, color=BRAND, edgecolor=PAGE_BG, linewidth=2, ax=ax, zorder=3, legend=False
)

# Style
ax.set_xlabel("Sales ($)", fontsize=20, color=INK)
ax.set_ylabel("Product Category", fontsize=20, color=INK)
ax.set_title("lollipop-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=18)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_xlim(0, max(values) * 1.08)

ax.xaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.yaxis.grid(False)
ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
