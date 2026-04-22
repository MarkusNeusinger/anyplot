""" pyplots.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Generate realistic stock price data with trend and volatility
np.random.seed(42)
n_days = 300
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")  # Business days

# Create a price series with trends and mean reversion
base_price = 150
returns = np.random.normal(0.0003, 0.015, n_days)  # Daily returns
# Add some trending behavior
trend = np.sin(np.linspace(0, 3 * np.pi, n_days)) * 0.001
returns = returns + trend
close = base_price * np.cumprod(1 + returns)

# Calculate SMAs
df = pd.DataFrame({"date": dates, "close": close})
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Price line - prominent
ax.plot(df["date"], df["close"], color="#306998", linewidth=2.5, label="Price", alpha=0.9)

# SMA lines with distinct colors
ax.plot(df["date"], df["sma_20"], color="#FFD43B", linewidth=2.5, label="SMA 20", linestyle="-")
ax.plot(df["date"], df["sma_50"], color="#E74C3C", linewidth=2.5, label="SMA 50", linestyle="-")
ax.plot(df["date"], df["sma_200"], color="#2ECC71", linewidth=2.5, label="SMA 200", linestyle="-")

# Styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.set_title("indicator-sma · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
