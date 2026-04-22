""" pyplots.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-07
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Generate realistic stock price data with Bollinger Bands
np.random.seed(42)
n_days = 120

# Generate realistic price movement using random walk
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.015, n_days)
price_base = 150
close = price_base * np.cumprod(1 + returns)

# Calculate Bollinger Bands (20-period SMA, 2 standard deviations)
window = 20
sma = pd.Series(close).rolling(window=window).mean()
std = pd.Series(close).rolling(window=window).std()
upper_band = sma + 2 * std
lower_band = sma - 2 * std

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot the filled area between bands (volatility envelope)
ax.fill_between(dates, lower_band, upper_band, alpha=0.2, color="#306998", label="Volatility Band (±2σ)")

# Plot upper and lower bands
ax.plot(dates, upper_band, color="#306998", linewidth=2, alpha=0.8)
ax.plot(dates, lower_band, color="#306998", linewidth=2, alpha=0.8)

# Plot middle band (SMA) as dashed line
ax.plot(dates, sma, color="#FFD43B", linewidth=2.5, linestyle="--", label="SMA (20-day)")

# Plot closing price prominently
ax.plot(dates, close, color="#1a1a2e", linewidth=2.5, label="Close Price")

# Labels and styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.set_title("indicator-bollinger · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Format x-axis dates
fig.autofmt_xdate(rotation=30)
ax.xaxis.set_major_locator(plt.MaxNLocator(8))

# Legend
ax.legend(fontsize=16, loc="upper left", framealpha=0.9)

# Grid
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
