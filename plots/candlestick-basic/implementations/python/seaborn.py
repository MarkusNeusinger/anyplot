"""anyplot.ai
candlestick-basic: Basic Candlestick Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.collections import PatchCollection
from matplotlib.patches import Patch, Rectangle


THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome tokens
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — finance semantic exception: profit/up→green, loss/down→red
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BULLISH_COLOR = IMPRINT_PALETTE[0]  # brand green
BEARISH_COLOR = IMPRINT_PALETTE[4]  # matte red

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

# Column constants
DATE = "Date"  # role: date
OPEN = "Open ($)"  # role: open
HIGH = "High ($)"  # role: high
LOW = "Low ($)"  # role: low
CLOSE = "Close ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 30
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")

price = 145.0
drift = np.concatenate(
    [
        np.linspace(0.4, 0.8, 12),  # Uptrend phase
        np.linspace(-0.1, -0.6, 18),  # Reversal and selloff
    ]
)
opens, highs, lows, closes = [], [], [], []
for i in range(n_days):
    change = drift[i] + np.random.randn() * 2.5
    volatility = abs(np.random.randn()) * 1.5 + 0.8
    open_price = price
    close_price = price + change
    high_price = max(open_price, close_price) + abs(np.random.randn()) * volatility
    low_price = min(open_price, close_price) - abs(np.random.randn()) * volatility
    opens.append(open_price)
    highs.append(high_price)
    lows.append(low_price)
    closes.append(close_price)
    price = close_price

df = pd.DataFrame({DATE: dates, OPEN: opens, HIGH: highs, LOW: lows, CLOSE: closes})

# Plot
x = np.arange(len(df))
bullish = (df[CLOSE] >= df[OPEN]).to_numpy()

# Canvas: 3200×1800 px (landscape 16:9)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Wicks (high-low range)
wick_colors = np.where(bullish, BULLISH_COLOR, BEARISH_COLOR)
ax.vlines(x, df[LOW], df[HIGH], colors=wick_colors, linewidth=0.8, alpha=0.8)

# Candle bodies (open-close range)
body_width = 0.6
min_body = 0.01 * (df[HIGH].max() - df[LOW].min())  # keeps a flat candle visible as a thin line
body_lo = np.minimum(df[OPEN], df[CLOSE])
body_h = np.maximum(np.abs(df[CLOSE] - df[OPEN]), min_body)
rects = [Rectangle((xi - body_width / 2, lo), body_width, h) for xi, lo, h in zip(x, body_lo, body_h, strict=True)]
bodies = PatchCollection(rects, facecolors=wick_colors, edgecolors=wick_colors, linewidths=0.4, alpha=0.9)
ax.add_collection(bodies)

# X-axis date ticks
tick_positions = np.arange(0, len(df), 5)
ax.set_xticks(tick_positions)
ax.set_xticklabels(df[DATE].dt.strftime("%b %d").iloc[tick_positions])

ax.set_xlabel(DATE, fontsize=10)
ax.set_ylabel("Price ($)", fontsize=10)
ax.set_title("candlestick-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", pad=12)
ax.tick_params(axis="both", labelsize=8, length=0)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.7, color=INK)
ax.xaxis.grid(False)
ax.set_axisbelow(True)

legend_handles = [
    Patch(facecolor=BULLISH_COLOR, edgecolor=BULLISH_COLOR, alpha=0.9, label="Bullish"),
    Patch(facecolor=BEARISH_COLOR, edgecolor=BEARISH_COLOR, alpha=0.9, label="Bearish"),
]
ax.legend(
    handles=legend_handles,
    fontsize=8,
    loc="upper right",
    framealpha=0.9,
    edgecolor=INK_SOFT,
    facecolor=ELEVATED_BG,
    labelcolor=INK,
)

ax.set_xlim(-0.8, len(df) - 0.2)
y_range = df[HIGH].max() - df[LOW].min()
y_pad = y_range * 0.06
ax.set_ylim(df[LOW].min() - y_pad, df[HIGH].max() + y_pad * 3.0)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
