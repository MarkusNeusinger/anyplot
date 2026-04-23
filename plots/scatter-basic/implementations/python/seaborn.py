"""anyplot.ai
scatter-basic: Basic Scatter Plot
Library: seaborn 0.13.2 | Python 3.14.4
Quality: pending | Updated: 2026-04-23
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data — marketing spend vs. quarterly sales revenue (r~0.75)
np.random.seed(42)
n = 220
marketing_spend = np.random.gamma(shape=2.2, scale=9.0, size=n) + 3
sales_revenue = 4.1 * marketing_spend + np.random.normal(0, 18, n) + 15
sales_revenue = np.clip(sales_revenue, 5, None)

df = pd.DataFrame({"Marketing Spend ($ thousands)": marketing_spend, "Quarterly Revenue ($ thousands)": sales_revenue})

# Plot
sns.set_theme(
    context="talk",
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
    },
)

fig, ax = plt.subplots(figsize=(16, 9))

sns.scatterplot(
    data=df,
    x="Marketing Spend ($ thousands)",
    y="Quarterly Revenue ($ thousands)",
    ax=ax,
    color=BRAND,
    s=130,
    alpha=0.7,
    edgecolor=PAGE_BG,
    linewidth=0.9,
)

# Style
ax.set_title("scatter-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)
ax.set_xlabel("Marketing Spend ($ thousands)", fontsize=20, color=INK, labelpad=12)
ax.set_ylabel("Quarterly Revenue ($ thousands)", fontsize=20, color=INK, labelpad=12)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, length=0)
ax.margins(x=0.04, y=0.06)
sns.despine(ax=ax)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
