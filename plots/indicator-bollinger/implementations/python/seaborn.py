"""anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-17
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

# Imprint palette: close price, middle band, outer bands
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
CLOSE_COLOR = IMPRINT_PALETTE[0]
SMA_COLOR = IMPRINT_PALETTE[1]
BAND_COLOR = IMPRINT_PALETTE[2]

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

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close Price"  # role: close
SMA = "20-Day SMA"  # role: sma
UPPER_BAND = "Upper Band (+2σ)"  # role: upper_band
LOWER_BAND = "Lower Band (−2σ)"  # role: lower_band

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 120
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Price path with two stretches of extra volatility
returns = np.random.normal(0.0005, 0.015, n_days)
prices = 150 * np.cumprod(1 + returns)
volatility_boost = np.zeros(n_days)
volatility_boost[30:50] = np.random.normal(0, 0.01, 20)
volatility_boost[80:95] = np.random.normal(0, 0.008, 15)
prices = prices * (1 + volatility_boost)

# Bollinger Bands: 20-period SMA with 2 standard deviations
close = pd.Series(prices)
sma = close.rolling(window=20).mean()
std = close.rolling(window=20).std()
df = pd.DataFrame({DATE: dates, CLOSE: close, SMA: sma, UPPER_BAND: sma + 2 * std, LOWER_BAND: sma - 2 * std}).dropna(
    subset=[SMA, UPPER_BAND, LOWER_BAND]
)

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

ax.fill_between(df[DATE], df[LOWER_BAND], df[UPPER_BAND], alpha=0.2, color=BAND_COLOR, linewidth=0, label="Band Range")
sns.lineplot(data=df, x=DATE, y=UPPER_BAND, color=BAND_COLOR, linewidth=1.1, label=UPPER_BAND, ax=ax)
sns.lineplot(data=df, x=DATE, y=LOWER_BAND, color=BAND_COLOR, linewidth=1.1, label=LOWER_BAND, ax=ax)
sns.lineplot(data=df, x=DATE, y=SMA, color=SMA_COLOR, linewidth=1.25, linestyle="--", label=SMA, ax=ax)
sns.lineplot(data=df, x=DATE, y=CLOSE, color=CLOSE_COLOR, linewidth=1.6, label=CLOSE, ax=ax)

# Style
ax.set_title("indicator-bollinger · python · seaborn · anyplot.ai", fontsize=12, fontweight="bold", pad=10)
ax.set_xlabel(DATE, fontsize=10)
ax.set_ylabel("Price (USD)", fontsize=10)
ax.tick_params(axis="both", labelsize=8)
fig.autofmt_xdate(rotation=30)

ax.legend(fontsize=8, loc="best", framealpha=0.95, frameon=True)
ax.yaxis.grid(True, linewidth=0.6)
ax.set_axisbelow(True)
sns.despine(ax=ax)

fig.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.16)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
