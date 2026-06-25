"""anyplot.ai
scatter-basic: Basic Scatter Plot
Library: seaborn | Python 3.13
Quality: pending | Updated: 2026-06-25
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1

# Data — marketing spend vs. quarterly sales revenue (r~0.75)
np.random.seed(42)
n = 220
marketing_spend = np.random.gamma(shape=2.2, scale=9.0, size=n) + 3
sales_revenue = 4.1 * marketing_spend + np.random.normal(0, 18, n) + 15
sales_revenue = np.clip(sales_revenue, 5, None)

df = pd.DataFrame({"Marketing Spend ($ thousands)": marketing_spend, "Quarterly Revenue ($ thousands)": sales_revenue})

# Plot
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
        "axes.linewidth": 0.9,
        "axes.grid": True,
        "axes.axisbelow": True,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.scatterplot(
    data=df,
    x="Marketing Spend ($ thousands)",
    y="Quarterly Revenue ($ thousands)",
    ax=ax,
    color=BRAND,
    s=100,
    alpha=0.7,
    edgecolor=PAGE_BG,
    linewidth=0.9,
)

# Style
ax.set_title("scatter-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=14)
ax.set_xlabel("Marketing Spend ($ thousands)", fontsize=10, color=INK, labelpad=10)
ax.set_ylabel("Quarterly Revenue ($ thousands)", fontsize=10, color=INK, labelpad=10)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
ax.margins(x=0.04, y=0.06)
sns.despine(ax=ax)

fig.subplots_adjust(left=0.11, right=0.97, top=0.93, bottom=0.13)

# Save — no bbox_inches='tight' (would trim the 3200×1800 canvas)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
