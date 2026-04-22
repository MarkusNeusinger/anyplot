""" pyplots.ai
line-stock-comparison: Stock Price Comparison Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Simulated daily stock prices for ~1 year (252 trading days)
np.random.seed(42)
n_days = 252
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")  # Business days

# Simulate price movements using geometric Brownian motion
stocks = {
    "AAPL": {"start": 185, "drift": 0.0008, "vol": 0.018},
    "GOOGL": {"start": 140, "drift": 0.0006, "vol": 0.020},
    "MSFT": {"start": 375, "drift": 0.0007, "vol": 0.016},
    "SPY": {"start": 475, "drift": 0.0004, "vol": 0.010},
}

prices = {}
for symbol, params in stocks.items():
    returns = np.random.normal(params["drift"], params["vol"], n_days)
    price_series = params["start"] * np.cumprod(1 + returns)
    prices[symbol] = price_series

# Normalize all series to 100 at the first date (rebased)
rebased = {}
for symbol, price_series in prices.items():
    rebased[symbol] = price_series / price_series[0] * 100

# Colors for each stock (using Python colors + distinct palette)
colors = {
    "AAPL": "#306998",  # Python Blue
    "GOOGL": "#E63946",  # Red
    "MSFT": "#2A9D8F",  # Teal
    "SPY": "#FFD43B",  # Python Yellow
}

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot each stock's rebased performance
for symbol in stocks.keys():
    ax.plot(dates, rebased[symbol], label=symbol, color=colors[symbol], linewidth=2.5)

# Add horizontal reference line at 100 (starting point)
ax.axhline(y=100, color="gray", linestyle="--", linewidth=1.5, alpha=0.7, label="Start (100)")

# Styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Rebased Value (Start = 100)", fontsize=20)
ax.set_title("line-stock-comparison · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")

# Format x-axis dates
fig.autofmt_xdate()

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
