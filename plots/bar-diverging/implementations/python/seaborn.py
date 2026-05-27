""" anyplot.ai
bar-diverging: Diverging Bar Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-08
"""

import os
import sys


sys.path = [p for p in sys.path if "implementations" not in p]  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# imprint semantic anchors
PROFIT_COLOR = "#009E73"  # green — profit
LOSS_COLOR = "#AE3030"  # red — loss

# Data - Quarterly profit/loss by business unit (in millions)
units = [
    "Cloud Services",
    "Data Analytics",
    "AI Solutions",
    "DevOps Platform",
    "Security Suite",
    "Enterprise Integration",
    "Mobile Apps",
    "Edge Computing",
    "Cybersecurity",
    "Support Services",
]

# Q1 profit/loss values (millions)
values = np.array([42, -18, 65, -25, 38, -12, 28, 52, -8, 15])

# Create DataFrame and sort by value
df = pd.DataFrame({"Unit": units, "Profit Loss (M)": values})
df = df.sort_values("Profit Loss (M)", ascending=True).reset_index(drop=True)

# Assign colors based on positive/negative
colors = [PROFIT_COLOR if x >= 0 else LOSS_COLOR for x in df["Profit Loss (M)"]]

# Configure seaborn theme
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
    },
)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Horizontal bar chart
sns.barplot(data=df, x="Profit Loss (M)", y="Unit", palette=colors, hue="Unit", legend=False, ax=ax, orient="h")

# Add vertical baseline at zero
ax.axvline(x=0, color=INK_SOFT, linewidth=2, zorder=2)

# Style
ax.set_xlabel("Profit/Loss ($ Millions)", fontsize=20, color=INK)
ax.set_ylabel("Business Unit", fontsize=20, color=INK)
ax.set_title("bar-diverging · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Grid on x-axis only
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.yaxis.grid(False)
ax.set_axisbelow(True)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
