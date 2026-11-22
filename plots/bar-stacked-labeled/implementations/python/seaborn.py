""" anyplot.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.colors import to_rgb


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: category
COST_TYPE = "Cost type"  # role: component
EXPENSE = "Expenses (thousand USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("expenses.csv")
departments = ["Engineering", "Marketing", "Sales", "Operations", "Support"]
df = pd.DataFrame(
    {
        DEPARTMENT: departments * 4,
        COST_TYPE: ["Salaries"] * 5 + ["Software"] * 5 + ["Travel"] * 5 + ["Equipment"] * 5,
        EXPENSE: [
            820,
            410,
            530,
            360,
            290,  # Salaries
            140,
            95,
            120,
            60,
            85,  # Software
            35,
            120,
            185,
            45,
            20,  # Travel
            110,
            40,
            55,
            130,
            50,  # Equipment
        ],
    }
)

# Plot: reads only df and the constants above
cost_types = list(dict.fromkeys(df[COST_TYPE]))
totals = df.groupby(DEPARTMENT, sort=False)[EXPENSE].sum()

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
sns.histplot(
    data=df,
    x=DEPARTMENT,
    weights=EXPENSE,
    hue=COST_TYPE,
    hue_order=cost_types,
    multiple="stack",
    shrink=0.7,
    palette=IMPRINT_PALETTE[: len(cost_types)],
    edgecolor=PAGE_BG,
    linewidth=0.8,
    alpha=1.0,
    legend=True,
    ax=ax,
)

# Segment labels inside segments tall enough to hold them, total labels above each stack
top = totals.max()
segment_min = top * 0.07
for container in ax.containers:
    for bar in container:
        if bar.get_height() >= segment_min:
            r, g, b = to_rgb(bar.get_facecolor())
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_y() + bar.get_height() / 2,
                f"{bar.get_height():.0f}",
                ha="center",
                va="center",
                fontsize=7,
                color="#1A1A17" if 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.5 else "#FFFFFF",
            )
for i, total in enumerate(totals):
    ax.annotate(
        f"${total:,.0f}K",
        xy=(i, total),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color=INK,
    )

# Style
ax.set_title("bar-stacked-labeled · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(DEPARTMENT, fontsize=10)
ax.set_ylabel(EXPENSE, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.set_ylim(0, top * 1.12)
ax.yaxis.grid(True, linewidth=0.8)
ax.set_axisbelow(True)
sns.despine(ax=ax)
sns.move_legend(
    ax,
    "upper right",
    title=COST_TYPE,
    fontsize=8,
    title_fontsize=9,
    framealpha=1.0,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
