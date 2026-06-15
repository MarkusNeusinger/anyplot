"""anyplot.ai
depth-order-book: Order Book Depth Chart
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-06-15
"""

import os
import sys


# Remove this script's directory from sys.path so 'import seaborn' finds the installed
# library rather than this file (Python adds the script dir to sys.path[0] automatically)
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _script_dir]

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Semantic colors — bid=green (buy/bullish), ask=red (sell/bearish)
BID_COLOR = "#009E73"  # Imprint palette position 1, brand green — buy side
ASK_COLOR = "#AE3030"  # Imprint palette position 5, matte red — sell side

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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data — BTC/USD order book snapshot (synthetic)
np.random.seed(42)
mid_price = 60_000.0
spread = 10.0  # $10 bid-ask spread
best_bid = mid_price - spread / 2  # 59995.0
best_ask = mid_price + spread / 2  # 60005.0
n_levels = 40
tick = 5.0  # $5 per price level

# Bid levels: descending from best_bid (index 0 = best bid, index 39 = worst bid)
bid_prices = best_bid - tick * np.arange(n_levels)
bid_qty = np.abs(np.random.normal(2.0, 1.0, n_levels))
bid_qty[14:17] += 16.0  # support wall at ~59925
bid_cum = np.cumsum(bid_qty)

# Ask levels: ascending from best_ask (index 0 = best ask, index 39 = worst ask)
ask_prices = best_ask + tick * np.arange(n_levels)
ask_qty = np.abs(np.random.normal(2.0, 1.0, n_levels))
ask_qty[17:20] += 20.0  # resistance wall at ~60090
ask_cum = np.cumsum(ask_qty)

# Bid sorted ascending for left-to-right staircase rendering
bid_x = bid_prices[::-1]  # [59800, ..., 59995]
bid_y = bid_cum[::-1]  # [total_cum, ..., min_cum]

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Bid area: semi-transparent fill + solid step outline
ax.fill_between(bid_x, bid_y, step="post", alpha=0.22, color=BID_COLOR)
ax.step(bid_x, bid_y, where="post", color=BID_COLOR, linewidth=1.8, label="Bids (Buy)")

# Ask area: semi-transparent fill + solid step outline
ax.fill_between(ask_prices, ask_cum, step="post", alpha=0.22, color=ASK_COLOR)
ax.step(ask_prices, ask_cum, where="post", color=ASK_COLOR, linewidth=1.8, label="Asks (Sell)")

# Mid price dashed vertical line
ax.axvline(mid_price, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.7)

# Annotate mid price and spread
y_top = max(bid_y.max(), ask_cum.max())
ax.annotate(
    f"Mid: ${mid_price:,.0f}\nSpread: ${spread:.0f}",
    xy=(mid_price, y_top * 0.80),
    ha="center",
    va="top",
    fontsize=8,
    color=INK_MUTED,
    bbox={"boxstyle": "round,pad=0.4", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "linewidth": 0.8, "alpha": 0.9},
)

# Style
title = "depth-order-book · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=10)
ax.set_xlabel("Price (USD)", fontsize=10, color=INK, labelpad=6)
ax.set_ylabel("Cumulative Volume (BTC)", fontsize=10, color=INK, labelpad=6)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_ylim(bottom=0)

legend = ax.legend(fontsize=8, framealpha=0.9, facecolor=ELEVATED_BG, edgecolor=INK_SOFT)
for text in legend.get_texts():
    text.set_color(INK_SOFT)

fig.subplots_adjust(left=0.10, right=0.97, top=0.92, bottom=0.13)

# Save to the script's own directory (no bbox_inches='tight' — see seaborn library guide)
plt.savefig(os.path.join(_script_dir, f"plot-{THEME}.png"), dpi=400, facecolor=PAGE_BG)
plt.close()
