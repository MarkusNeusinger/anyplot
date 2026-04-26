"""anyplot.ai
dumbbell-basic: Basic Dumbbell Chart
Library: seaborn | Python 3.13
Quality: pending | Updated: 2026-04-26
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
RULE = INK  # alpha applied via grid.alpha

BEFORE_COLOR = "#009E73"  # Okabe-Ito 1 — first series, brand
AFTER_COLOR = "#D55E00"  # Okabe-Ito 2

# Data — Employee satisfaction scores before and after policy changes
df = pd.DataFrame(
    {
        "Department": [
            "Engineering",
            "Marketing",
            "Sales",
            "HR",
            "Finance",
            "Operations",
            "Legal",
            "Customer Support",
            "Research",
            "IT",
        ],
        "Before": [65, 58, 72, 61, 55, 68, 52, 70, 63, 59],
        "After": [78, 75, 85, 80, 71, 82, 68, 88, 79, 76],
    }
)
df["Difference"] = df["After"] - df["Before"]
df = df.sort_values("Difference", ascending=True).reset_index(drop=True)

# Theme-adaptive seaborn styling
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
        "grid.color": RULE,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Connecting lines (drawn first, sit beneath dots)
for i, row in df.iterrows():
    ax.plot([row["Before"], row["After"]], [i, i], color=INK_SOFT, alpha=0.5, linewidth=2, zorder=1)

# Dots — seaborn scatterplot for both ends
sns.scatterplot(
    x=df["Before"],
    y=range(len(df)),
    color=BEFORE_COLOR,
    s=420,
    label="Before policy change",
    edgecolor=PAGE_BG,
    linewidth=1.5,
    ax=ax,
    zorder=2,
)
sns.scatterplot(
    x=df["After"],
    y=range(len(df)),
    color=AFTER_COLOR,
    s=420,
    label="After policy change",
    edgecolor=PAGE_BG,
    linewidth=1.5,
    ax=ax,
    zorder=3,
)

# Style
ax.set_yticks(range(len(df)))
ax.set_yticklabels(df["Department"])
ax.set_xlabel("Employee Satisfaction Score (%)", fontsize=20, color=INK)
ax.set_ylabel("")
ax.set_title(
    "Employee Satisfaction · dumbbell-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20
)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(45, 95)
ax.set_ylim(-0.7, len(df) - 0.3)

sns.despine(ax=ax, top=True, right=True)
ax.xaxis.grid(True, linewidth=0.8)
ax.yaxis.grid(False)

legend = ax.legend(fontsize=16, loc="lower right", frameon=True, framealpha=1.0, borderpad=0.8)
for text in legend.get_texts():
    text.set_color(INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
