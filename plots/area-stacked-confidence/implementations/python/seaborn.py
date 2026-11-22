"""anyplot.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-18
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

# Imprint palette: all eight positions, one per series in stack order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names; the lists run bottom layer first
QUARTER = "Quarter"  # role: x
ASSET = "Asset Class"  # role: category
ALLOCATION = ["Stocks", "Bonds", "Commodities", "Real Estate"]  # role: y
LOWER = ["Stocks lower", "Bonds lower", "Commodities lower", "Real Estate lower"]  # role: y_lower
UPPER = ["Stocks upper", "Bonds upper", "Commodities upper", "Real Estate upper"]  # role: y_upper

# Data: replace this block with your own table, for example df = pd.read_csv("allocation.csv")
# One row per quarter; one column per asset class for its share, plus its lower and upper bound.
np.random.seed(42)
quarters = pd.date_range("2020-01-01", periods=24, freq="QE")
n = len(quarters)
values = [
    np.linspace(45, 50, n) + np.random.randn(n) * 2,
    np.linspace(30, 28, n) + np.random.randn(n) * 1.5,
    np.linspace(15, 12, n) + np.random.randn(n) * 1,
    np.linspace(10, 10, n) + np.random.randn(n) * 0.8,
]
# 90% interval half-widths: estimates get tighter in recent years
halves = [np.linspace(4, 2.5, n), np.linspace(3, 2, n), np.linspace(2.5, 1.5, n), np.linspace(2, 1, n)]
df = pd.DataFrame(
    {
        QUARTER: quarters,
        **dict(zip(ALLOCATION, values, strict=True)),
        **{col: v - h for col, v, h in zip(LOWER, values, halves, strict=True)},
        **{col: v + h for col, v, h in zip(UPPER, values, halves, strict=True)},
    }
)

# Plot: reads only df and the constants above
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

# Stacked edges: central value of each series on top of the layers below it
index = pd.DatetimeIndex(df[QUARTER])
value = df[ALLOCATION].set_axis(index)
lower = df[LOWER].set_axis(index, axis=0).set_axis(ALLOCATION, axis=1)
upper = df[UPPER].set_axis(index, axis=0).set_axis(ALLOCATION, axis=1)
order = list(ALLOCATION)
top_edge = value.cumsum(axis=1)
base_edge = top_edge - value  # where each layer starts: the edge of the layer below

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Draw from the top layer down so lower layers and their bands stay in front
for i in reversed(range(len(order))):
    name = order[i]
    color = IMPRINT_PALETTE[i]
    ax.fill_between(
        value.index, base_edge[name] + lower[name], base_edge[name] + upper[name], color=color, alpha=0.25, linewidth=0
    )
    ax.fill_between(value.index, base_edge[name], top_edge[name], color=color, alpha=0.8, label=name)

# Stacked central value of each series as an edge line
for i, name in enumerate(order):
    sns.lineplot(x=value.index, y=top_edge[name], color=IMPRINT_PALETTE[i], linewidth=1, alpha=0.9, ax=ax)

# Style
ax.set_title("area-stacked-confidence · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(QUARTER, fontsize=10, color=INK)
ax.set_ylabel("Portfolio Allocation (%)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.tick_params(axis="x", labelrotation=45)
ax.set_ylim(0, np.nanmax((base_edge + upper).to_numpy()) * 1.15)
ax.margins(x=0.01)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Legend lists the top layer first, matching the stack
handles, labels = ax.get_legend_handles_labels()
legend = ax.legend(
    handles[::-1],
    labels[::-1],
    loc="upper left",
    ncol=len(order),
    fontsize=8,
    title=f"{ASSET} (shaded bands = 90% CI)",
    title_fontsize=8,
    framealpha=0.95,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
legend.get_title().set_color(INK)
for text in legend.get_texts():
    text.set_color(INK)

fig.subplots_adjust(left=0.08, right=0.98, top=0.93, bottom=0.2)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
