"""anyplot.ai
bar-grouped: Grouped Bar Chart
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-10-23
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NEAR_TIE = 0.05  # a gap below this share of the tallest bar counts as a near-tie

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: category
PRODUCT_LINE = "Product line"  # role: group
SALES = "Sales (thousand USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("sales.csv")
df = pd.DataFrame(
    {
        QUARTER: ["Q1", "Q2", "Q3", "Q4"] * 3,
        PRODUCT_LINE: ["Electronics"] * 4 + ["Clothing"] * 4 + ["Home & Garden"] * 4,
        SALES: [245, 312, 287, 425, 178, 195, 285, 310, 125, 210, 195, 165],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=QUARTER, columns=PRODUCT_LINE, values=SALES, sort=False)
values = table.to_numpy(dtype=float)
x = np.arange(len(table.index))
width = 0.8 / len(table.columns)
top = np.nanmax(values)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
for i, line in enumerate(table.columns):
    offset = (i - (len(table.columns) - 1) / 2) * width
    ax.bar(x + offset, table[line], width, label=line, color=IMPRINT[i], edgecolor=INK_SOFT, linewidth=1.0)

# Callout: the target is chosen by a rule over df and drawn only when the claim holds
if len(table.columns) > 1:
    ranked = np.sort(np.where(np.isnan(values), -np.inf, values), axis=1)
    gaps = ranked[:, -1] - ranked[:, -2]
    gaps = np.where(np.isfinite(gaps), gaps, np.inf)
    tie = int(np.argmin(gaps))
    if gaps[tie] <= NEAR_TIE * top:
        ax.annotate(
            f"Near-tie in {table.index[tie]}",
            xy=(x[tie], ranked[tie, -1]),
            xytext=(0, 14),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color=INK_SOFT,
            style="italic",
        )

# Style
ax.set_title("bar-grouped · python · matplotlib · anyplot.ai", fontsize=13, fontweight="bold", color=INK)
ax.set_xticks(x, table.index)
ax.set_xlabel(QUARTER, color=INK)
ax.set_ylabel(SALES, color=INK)
ax.set_ylim(0, top * 1.15)
ax.legend(title=PRODUCT_LINE, fontsize=8)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
