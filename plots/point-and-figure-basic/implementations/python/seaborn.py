"""anyplot.ai
point-and-figure-basic: Point and Figure Chart
Library: seaborn | Python 3.13
Quality: pending | Updated: 2026-05-20
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
BULL_COLOR = "#009E73"  # Okabe-Ito position 1 — X columns (bullish)
BEAR_COLOR = "#D55E00"  # Okabe-Ito position 2 — O columns (bearish)

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

# Data — synthetic biotech stock over 300 trading days
np.random.seed(42)
n_days = 300
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")

base_price = 80.0
returns = np.random.normal(0.001, 0.018, n_days)
returns[40:90] += 0.006
returns[130:180] -= 0.006
returns[230:270] += 0.005

prices = base_price * np.exp(np.cumsum(returns))
close_prices = pd.Series(prices)

# Point and Figure calculation — 3-box reversal, $2 box size
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

# Build plot DataFrame
plot_rows = []
for col_idx, boxes, direction in pnf_columns:
    for box in boxes:
        plot_rows.append({"column": col_idx, "price": box, "direction": direction})

plot_df = pd.DataFrame(plot_rows)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

x_data = plot_df[plot_df["direction"] == "X"]
o_data = plot_df[plot_df["direction"] == "O"]

if not x_data.empty:
    sns.scatterplot(
        data=x_data, x="column", y="price", marker="x", s=220, linewidth=2.5, color=BULL_COLOR, ax=ax, legend=False
    )

if not o_data.empty:
    sns.scatterplot(
        data=o_data,
        x="column",
        y="price",
        marker="o",
        s=170,
        facecolors="none",
        edgecolor=BEAR_COLOR,
        linewidth=2.5,
        ax=ax,
        legend=False,
    )

# Style
ax.set_xlabel("Column (Reversals)", fontsize=10, color=INK)
ax.set_ylabel("Price ($)", fontsize=10, color=INK)
ax.set_title("point-and-figure-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Y-axis ticks aligned to box boundaries
price_min = plot_df["price"].min() - box_size
price_max = plot_df["price"].max() + box_size
yticks = np.arange(int(price_min / box_size) * box_size, price_max + box_size, box_size * 2)
ax.set_yticks(yticks)
ax.set_ylim(price_min, price_max)
ax.set_xlim(-0.5, plot_df["column"].max() + 0.5)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Legend
ax.scatter([], [], marker="x", s=220, linewidth=2.5, color=BULL_COLOR, label="X — Rising")
ax.scatter([], [], marker="o", s=170, facecolors="none", edgecolor=BEAR_COLOR, linewidth=2.5, label="O — Falling")
ax.legend(loc="upper left", fontsize=8, frameon=True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
