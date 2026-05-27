""" anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-13
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

BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT = "#C475FD"  # Okabe-Ito position 2

# Data: Stock price with 20-day moving average (domain differs from temp/traffic)
np.random.seed(42)

# Generate 252 trading days (1 year) of stock price data
dates = pd.date_range(start="2024-01-01", periods=252, freq="B")

# Stock price with uptrend, volatility, and correction pattern
day_index = np.arange(252)
base_price = 100

# Uptrend with noise and correction
trend = base_price + 0.05 * day_index + 3 * np.sin(2 * np.pi * day_index / 252)
volatility = np.random.normal(0, 2.5, 252)
stock_price = trend + volatility

# Create DataFrame
df = pd.DataFrame({"date": dates, "price": stock_price})

# Calculate 20-day moving average (typical trading analysis window)
df["moving_avg"] = df["price"].rolling(window=20, center=False).mean()

# Configure seaborn with theme-adaptive colors
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
sns.set_context("talk", font_scale=1.1)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Plot raw data as semi-transparent line with slight prominence boost
sns.lineplot(data=df, x="date", y="price", ax=ax, color=BRAND, alpha=0.5, linewidth=2, label="Daily Price")

# Plot moving average as prominent smooth line
sns.lineplot(data=df, x="date", y="moving_avg", ax=ax, color=ACCENT, linewidth=4, label="20-Day Moving Average")

# Styling
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Stock Price ($)", fontsize=20, color=INK)
ax.set_title("line-timeseries-rolling · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Rotate x-axis labels for readability
plt.xticks(rotation=30, ha="right")

# Legend styling with reduced framealpha
ax.legend(fontsize=16, loc="upper left", framealpha=0.85, edgecolor=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(INK_SOFT)

# Grid on both axes for time series readability
ax.grid(True, alpha=0.15, linewidth=0.8, axis="both")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
