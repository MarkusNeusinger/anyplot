""" anyplot.ai
step-basic: Basic Step Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 88/100 | Updated: 2026-04-30
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
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Monthly cumulative sales figures
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
months = np.arange(1, 13)
monthly_sales = np.array([45, 52, 68, 75, 82, 95, 88, 92, 105, 115, 130, 155])
cumulative_sales = np.cumsum(monthly_sales)

df = pd.DataFrame({"Month": months, "Cumulative Sales ($K)": cumulative_sales})

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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(data=df, x="Month", y="Cumulative Sales ($K)", color=BRAND, linewidth=3, drawstyle="steps-post", ax=ax)

# Markers at each data point to show where changes occur
ax.scatter(df["Month"], df["Cumulative Sales ($K)"], s=150, color=BRAND, edgecolors=PAGE_BG, linewidth=2, zorder=5)

# Style
ax.set_xlabel("Month", fontsize=20, color=INK)
ax.set_ylabel("Cumulative Sales ($K)", fontsize=20, color=INK)
ax.set_title("step-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_xticks(months)
ax.set_xticklabels(month_names)
ax.set_ylim(0, cumulative_sales[-1] * 1.15)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
