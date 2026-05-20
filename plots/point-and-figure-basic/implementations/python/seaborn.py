"""anyplot.ai
point-and-figure-basic: Point and Figure Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BULL_COLOR = "#009E73"  # Okabe-Ito pos 1 — X columns (bullish)
BEAR_COLOR = "#D55E00"  # Okabe-Ito pos 2 — O columns (bearish)

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

# Synthetic biotech stock over 300 trading days
np.random.seed(42)
n_days = 300

base_price = 80.0
returns = np.random.normal(0.001, 0.018, n_days)
returns[40:90] += 0.006
returns[130:180] -= 0.006
returns[230:270] += 0.005

prices = base_price * np.exp(np.cumsum(returns))
close_prices = pd.Series(prices)

# Point and Figure — 3-box reversal, $2 box size
box_size = 2.0
reversal = 3

pnf_columns = []
current_direction = None
current_col_boxes = []
col_index = 0
first_box = round(close_prices.iloc[0] / box_size) * box_size

for price in close_prices:
    rounded_price = round(price / box_size) * box_size

    if current_direction is None:
        current_col_boxes = [first_box]
        if rounded_price > first_box:
            current_direction = "X"
            while current_col_boxes[-1] + box_size <= rounded_price:
                current_col_boxes.append(current_col_boxes[-1] + box_size)
        elif rounded_price < first_box:
            current_direction = "O"
            while current_col_boxes[-1] - box_size >= rounded_price:
                current_col_boxes.append(current_col_boxes[-1] - box_size)
        continue

    if current_direction == "X":
        top_box = max(current_col_boxes)
        if rounded_price >= top_box + box_size:
            while current_col_boxes[-1] + box_size <= rounded_price:
                current_col_boxes.append(current_col_boxes[-1] + box_size)
        elif rounded_price <= top_box - reversal * box_size:
            pnf_columns.append((col_index, list(current_col_boxes), "X"))
            col_index += 1
            start_box = top_box - box_size
            current_col_boxes = [start_box]
            current_direction = "O"
            while current_col_boxes[-1] - box_size >= rounded_price:
                current_col_boxes.append(current_col_boxes[-1] - box_size)
    else:
        bottom_box = min(current_col_boxes)
        if rounded_price <= bottom_box - box_size:
            while current_col_boxes[-1] - box_size >= rounded_price:
                current_col_boxes.append(current_col_boxes[-1] - box_size)
        elif rounded_price >= bottom_box + reversal * box_size:
            pnf_columns.append((col_index, list(current_col_boxes), "O"))
            col_index += 1
            start_box = bottom_box + box_size
            current_col_boxes = [start_box]
            current_direction = "X"
            while current_col_boxes[-1] + box_size <= rounded_price:
                current_col_boxes.append(current_col_boxes[-1] + box_size)

if current_col_boxes:
    pnf_columns.append((col_index, current_col_boxes, current_direction or "X"))

# Build DataFrame with series labels for seaborn hue encoding
plot_rows = []
for col_idx, boxes, direction in pnf_columns:
    series = "X — Rising" if direction == "X" else "O — Falling"
    for box in boxes:
        plot_rows.append({"column": col_idx, "price": box, "series": series})

plot_df = pd.DataFrame(plot_rows)

# 45-degree trend line anchors
o_bottoms = [(ci, min(boxes)) for ci, boxes, d in pnf_columns if d == "O"]
x_tops = [(ci, max(boxes)) for ci, boxes, d in pnf_columns if d == "X"]

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

price_min = plot_df["price"].min() - box_size
price_max = plot_df["price"].max() + box_size
col_max = int(plot_df["column"].max())

# Seaborn hue + style dual-encoding: direction → color (palette) + marker shape
sns.scatterplot(
    data=plot_df,
    x="column",
    y="price",
    hue="series",
    style="series",
    hue_order=["X — Rising", "O — Falling"],
    style_order=["X — Rising", "O — Falling"],
    palette={"X — Rising": BULL_COLOR, "O — Falling": BEAR_COLOR},
    markers={"X — Rising": "X", "O — Falling": "o"},
    s=200,
    linewidth=2.5,
    legend=False,
    ax=ax,
)

# 45-degree support trend line — ascending from the lowest O-column bottom
if o_bottoms:
    supp_col, supp_price = min(o_bottoms, key=lambda t: t[1])
    x_end = min(col_max + 0.5, supp_col + (price_max - supp_price) / box_size)
    if x_end > supp_col:
        ax.plot(
            [supp_col, x_end],
            [supp_price, supp_price + (x_end - supp_col) * box_size],
            "--",
            color=BULL_COLOR,
            alpha=0.55,
            linewidth=1.5,
            zorder=1,
        )
        ax.annotate(
            "Support",
            xy=(supp_col, supp_price),
            xytext=(4, -12),
            textcoords="offset points",
            fontsize=7,
            color=BULL_COLOR,
            alpha=0.85,
        )

# 45-degree resistance trend line — descending from the highest X-column top
if x_tops:
    res_col, res_price = max(x_tops, key=lambda t: t[1])
    x_end = min(col_max + 0.5, res_col + (res_price - price_min) / box_size)
    if x_end > res_col:
        ax.plot(
            [res_col, x_end],
            [res_price, res_price - (x_end - res_col) * box_size],
            "--",
            color=BEAR_COLOR,
            alpha=0.55,
            linewidth=1.5,
            zorder=1,
        )
        ax.annotate(
            "Resistance",
            xy=(res_col, res_price),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7,
            color=BEAR_COLOR,
            alpha=0.85,
        )

# Style
ax.set_xlabel("Column (Reversals)", fontsize=10, color=INK)
ax.set_ylabel("Price ($)", fontsize=10, color=INK)
ax.set_title("point-and-figure-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

yticks = np.arange(int(price_min / box_size) * box_size, price_max + box_size, box_size * 2)
ax.set_yticks(yticks)
ax.set_ylim(price_min, price_max)
ax.set_xlim(-0.5, col_max + 0.5)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Legend: hollow-O convention + trend line entries
legend_handles = [
    Line2D([0], [0], marker="X", color=BULL_COLOR, markersize=8, linewidth=0, markeredgewidth=2.5),
    Line2D(
        [0], [0], marker="o", color=BEAR_COLOR, markersize=8, linewidth=0, markerfacecolor="none", markeredgewidth=2.5
    ),
    Line2D([0], [0], linestyle="--", color=BULL_COLOR, alpha=0.7, linewidth=1.5),
    Line2D([0], [0], linestyle="--", color=BEAR_COLOR, alpha=0.7, linewidth=1.5),
]
legend_labels = ["X — Rising", "O — Falling", "Support (45°)", "Resistance (45°)"]
leg = ax.legend(
    handles=legend_handles,
    labels=legend_labels,
    loc="upper left",
    fontsize=8,
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
for text in leg.get_texts():
    text.set_color(INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
