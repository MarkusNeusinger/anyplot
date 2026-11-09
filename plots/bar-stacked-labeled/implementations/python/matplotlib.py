"""anyplot.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgb


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per component in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LABEL_MIN_SHARE = 0.07  # segments shorter than this share of the value axis get no inside label
DARK_TEXT_LUMINANCE = 0.55  # fills brighter than this take dark segment labels, darker ones white

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: category
PRODUCT_LINE = "Product line"  # role: component
REVENUE = "Revenue ($ millions)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
df = pd.DataFrame(
    {
        QUARTER: ["Q1", "Q2", "Q3", "Q4"] * 4,
        PRODUCT_LINE: ["Software"] * 4 + ["Hardware"] * 4 + ["Services"] * 4 + ["Support"] * 4,
        REVENUE: [45, 52, 58, 62, 30, 28, 35, 42, 25, 32, 38, 45, 15, 18, 22, 28],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=QUARTER, columns=PRODUCT_LINE, values=REVENUE, sort=False).astype(float)
filled = table.fillna(0)
bottoms = filled.cumsum(axis=1) - filled
totals = table.sum(axis=1)
y_top = totals.max() * 1.15
x = np.arange(len(table.index))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, line in enumerate(table.columns):
    color = IMPRINT_PALETTE[i]
    bars = ax.bar(
        x, table[line], 0.6, bottom=bottoms[line], label=line, color=color, edgecolor=PAGE_BG, linewidth=1.2, zorder=2
    )
    luminance = np.dot(to_rgb(color), [0.299, 0.587, 0.114])
    text_color = "#FFFFFF" if luminance < DARK_TEXT_LUMINANCE else "#1A1A17"
    segment_labels = [f"${v:,.0f}M" if v >= LABEL_MIN_SHARE * y_top else "" for v in table[line].fillna(0)]
    ax.bar_label(bars, labels=segment_labels, label_type="center", fontsize=7, color=text_color)

# Total labels: bold, directly above every complete stack
for xi, total in zip(x, totals, strict=True):
    ax.annotate(
        f"${total:,.0f}M",
        xy=(xi, total),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color=INK,
    )

# Style
ax.set_title("bar-stacked-labeled · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xticks(x, table.index)
ax.set_xlabel(QUARTER, fontsize=10, color=INK)
ax.set_ylabel(REVENUE, fontsize=10, color=INK)
ax.set_ylim(0, y_top)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.tick_params(axis="x", length=0)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK, zorder=0)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Legend lists the components top-down, matching the stack order
handles, labels = ax.get_legend_handles_labels()
leg = ax.legend(
    handles[::-1],
    labels[::-1],
    title=PRODUCT_LINE,
    fontsize=8,
    title_fontsize=8,
    loc="upper left",
    bbox_to_anchor=(1.01, 1),
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
