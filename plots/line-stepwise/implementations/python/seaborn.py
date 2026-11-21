""" anyplot.ai
line-stepwise: Step Line Plot
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, first series always #009E73
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
    },
)

# Constants
TITLE = "line-stepwise · python · seaborn · anyplot.ai"

TRADING_DAY = "Trading Day"  # role: x
STOCK_PRICE = "Stock Price ($)"  # role: y

# Data - closing stock price stepping over trading days
df = pd.DataFrame(
    {
        TRADING_DAY: range(31),
        STOCK_PRICE: [
            150.00,
            150.00,
            150.00,
            152.50,
            152.50,
            152.50,
            155.00,
            155.00,
            155.00,
            153.25,
            153.25,
            153.25,
            156.75,
            156.75,
            156.75,
            158.50,
            158.50,
            159.25,
            159.25,
            159.25,
            161.00,
            161.00,
            161.00,
            159.50,
            159.50,
            162.00,
            162.00,
            162.00,
            164.50,
            164.50,
            163.75,
        ],
    }
)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

sns.lineplot(
    data=df,
    x=TRADING_DAY,
    y=STOCK_PRICE,
    ax=ax,
    drawstyle="steps-post",
    linewidth=2,
    color=IMPRINT_PALETTE[0],
    marker="o",
    markersize=4,
    markerfacecolor=IMPRINT_PALETTE[0],
    markeredgecolor=PAGE_BG,
    markeredgewidth=0.5,
)

ax.set_xlabel(TRADING_DAY, fontsize=10)
ax.set_ylabel(STOCK_PRICE, fontsize=10)
ax.set_title(TITLE, fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8)

# Axis limits derived from the data
x_pad = len(df) * 0.03
y_lo, y_hi = df[STOCK_PRICE].min(), df[STOCK_PRICE].max()
y_pad = (y_hi - y_lo) * 0.1
ax.set_xlim(df[TRADING_DAY].min() - x_pad, df[TRADING_DAY].max() + x_pad)
ax.set_ylim(y_lo - y_pad, y_hi + y_pad)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
sns.despine(ax=ax)

fig.tight_layout()
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
