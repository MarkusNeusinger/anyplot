"""anyplot.ai
bar-stacked: Stacked Bar Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per component in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: category
PRODUCT = "Product line"  # role: component
REVENUE = "Revenue (million USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
df = pd.DataFrame(
    {
        QUARTER: ["Q1", "Q2", "Q3", "Q4"] * 4,
        PRODUCT: ["Software"] * 4 + ["Hardware"] * 4 + ["Services"] * 4 + ["Support"] * 4,
        REVENUE: [45, 52, 48, 68, 32, 28, 35, 42, 28, 31, 38, 35, 15, 18, 20, 22],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=QUARTER, columns=PRODUCT, values=REVENUE, sort=False)
x = np.arange(len(table.index))
totals = table.sum(axis=1)
top = totals.max()

title = "bar-stacked · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

bottom = np.zeros(len(table.index))
for i, component in enumerate(table.columns):
    values = table[component].to_numpy()
    ax.bar(x, values, 0.6, bottom=bottom, label=component, color=IMPRINT_PALETTE[i], edgecolor=PAGE_BG, linewidth=1.0)
    bottom += np.nan_to_num(values)

# Total above each complete stack
for xi, total in zip(x, totals, strict=True):
    ax.annotate(
        f"${total:g}M",
        xy=(xi, total),
        xytext=(0, 5),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color=INK,
    )

# Style
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.set_xlabel(QUARTER, fontsize=10, color=INK)
ax.set_ylabel(REVENUE, fontsize=10, color=INK)
ax.set_xticks(x, table.index)
ax.set_ylim(0, top * 1.12)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

leg = ax.legend(title=PRODUCT, fontsize=8, title_fontsize=8, loc="upper left", bbox_to_anchor=(1.02, 1))
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.85, top=0.91, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
