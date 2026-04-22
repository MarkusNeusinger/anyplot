""" pyplots.ai
indicator-macd: MACD Technical Indicator Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Generate synthetic stock price data and calculate MACD
np.random.seed(42)

# Create 150 trading days of price data (need 120 for display + 26 for EMA warmup)
n_days = 150
dates = pd.date_range("2024-06-01", periods=n_days, freq="B")

# Generate realistic price movement with trend and volatility
returns = np.random.normal(0.0005, 0.015, n_days)  # Daily returns
price = 100 * np.cumprod(1 + returns)


# Calculate EMAs for MACD
def ema(data, span):
    return pd.Series(data).ewm(span=span, adjust=False).mean().values


ema_12 = ema(price, 12)
ema_26 = ema(price, 26)

# Calculate MACD components
macd_line = ema_12 - ema_26
signal_line = ema(macd_line, 9)
histogram = macd_line - signal_line

# Use only the last 120 days (after EMAs have stabilized)
start_idx = 30
dates = dates[start_idx:]
macd_line = macd_line[start_idx:]
signal_line = signal_line[start_idx:]
histogram = histogram[start_idx:]

# Create the plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot histogram as bars with green (positive) and red (negative)
colors = ["#2ECC71" if h >= 0 else "#E74C3C" for h in histogram]
ax.bar(dates, histogram, color=colors, alpha=0.7, width=0.8, label="Histogram")

# Plot MACD and Signal lines
ax.plot(dates, macd_line, color="#306998", linewidth=2.5, label="MACD (12, 26)")
ax.plot(dates, signal_line, color="#FFD43B", linewidth=2.5, label="Signal (9)")

# Add zero reference line
ax.axhline(y=0, color="gray", linestyle="--", linewidth=1.5, alpha=0.7)

# Styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("MACD Value", fontsize=20)
ax.set_title("indicator-macd · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")

# Format x-axis dates
fig.autofmt_xdate(rotation=45)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
