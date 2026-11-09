""" anyplot.ai
lollipop-grouped: Grouped Lollipop Chart
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-09
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

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
REGION = "Region"  # role: category
PRODUCT_LINE = "Product line"  # role: series
REVENUE = "Revenue ($ millions)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
df = pd.DataFrame(
    {
        REGION: ["North", "South", "East", "West"] * 3,
        PRODUCT_LINE: ["Electronics"] * 4 + ["Furniture"] * 4 + ["Clothing"] * 4,
        REVENUE: [4.2, 3.1, 5.5, 2.8, 2.8, 3.5, 2.2, 4.1, 3.5, 2.9, 3.8, 3.2],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=REGION, columns=PRODUCT_LINE, values=REVENUE, sort=False)
table = table.loc[table.sum(axis=1).sort_values(ascending=False).index]  # regions by total revenue
x = np.arange(len(table.index))
step = 0.66 / len(table.columns)
top = np.nanmax(table.to_numpy())

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, line in enumerate(table.columns):
    x_pos = x + (i - (len(table.columns) - 1) / 2) * step
    ax.vlines(x_pos, 0, table[line], color=IMPRINT_PALETTE[i], linewidth=2, zorder=2)
    ax.scatter(
        x_pos, table[line], s=110, color=IMPRINT_PALETTE[i], edgecolors=PAGE_BG, linewidths=1.2, zorder=3, label=line
    )

# Style
ax.axhline(0, color=INK_SOFT, linewidth=1.0, zorder=1)
ax.set_title("lollipop-grouped · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xticks(x, table.index)
ax.set_xlabel(f"{REGION} (sorted by total)", fontsize=10, color=INK)
ax.set_ylabel(REVENUE, fontsize=10, color=INK)
ax.set_ylim(0, top * 1.18)
ax.set_xlim(-0.6, len(table.index) - 0.4)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.tick_params(axis="x", length=0)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, color=INK, linewidth=0.8)
ax.set_axisbelow(True)

leg = ax.legend(
    title=PRODUCT_LINE, fontsize=8, title_fontsize=8, loc="upper right", ncols=len(table.columns), frameon=True
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

fig.subplots_adjust(left=0.08, right=0.98, top=0.9, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
