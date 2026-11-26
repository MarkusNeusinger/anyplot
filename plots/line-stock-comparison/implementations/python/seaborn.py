"""anyplot.ai
line-stock-comparison: Stock Price Comparison Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-23
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

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Set seaborn theme BEFORE figure creation
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
sns.set_context("notebook", font_scale=1.0)

# Constants
BASE = 100  # every series is rebased to this value on the first date

# Columns: set these to your table's column names
DATE = "Date"  # role: date
SYMBOL = "Symbol"  # role: symbol
PRICE = "Price (USD)"  # role: price

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
rng = np.random.default_rng(42)
dates = pd.date_range("2024-01-01", periods=252, freq="B")  # business days
# (daily drift, daily volatility) per symbol; SPY is the lower-volatility index
params = {"AAPL": (0.0008, 0.018), "GOOGL": (0.0006, 0.022), "MSFT": (0.0010, 0.016), "SPY": (0.0005, 0.010)}
start_price = {"AAPL": 185.0, "GOOGL": 140.0, "MSFT": 375.0, "SPY": 470.0}
frames = []
for symbol, (drift, volatility) in params.items():
    log_returns = rng.normal(drift, volatility, len(dates))
    frames.append(
        pd.DataFrame({DATE: dates, SYMBOL: symbol, PRICE: start_price[symbol] * np.exp(np.cumsum(log_returns))})
    )
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
df = df.sort_values([SYMBOL, DATE], kind="stable")
rebased = df[PRICE] / df.groupby(SYMBOL, sort=False)[PRICE].transform("first") * BASE
df = df.assign(**{"Rebased price": rebased})
REBASED = "Rebased price"

symbols = list(df[SYMBOL].unique())
palette_map = {symbol: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, symbol in enumerate(symbols)}

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(data=df, x=DATE, y=REBASED, hue=SYMBOL, hue_order=symbols, palette=palette_map, linewidth=2.5, ax=ax)

# Reference line at the common starting value
ax.axhline(y=BASE, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.6, zorder=0)

# Style
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel(f"Rebased price (start = {BASE})", fontsize=10, color=INK)
ax.set_title("line-stock-comparison · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Legend outside the plot on the right, clear of the lines
sns.move_legend(ax, "upper left", bbox_to_anchor=(1.01, 1.0), title=SYMBOL, fontsize=8, title_fontsize=8)

# Grid — y-axis only for line chart
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.set_axisbelow(True)

# Spines — remove top and right (seaborn-idiomatic)
sns.despine(ax=ax)

# Rotate x-axis dates for readability
fig.autofmt_xdate(rotation=30)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
