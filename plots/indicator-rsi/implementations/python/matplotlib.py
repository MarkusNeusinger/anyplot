""" pyplots.ai
indicator-rsi: RSI Technical Indicator Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Generate synthetic stock price data and calculate RSI
np.random.seed(42)
n_periods = 120
dates = pd.date_range("2024-01-01", periods=n_periods, freq="D")

# Generate realistic price movements (random walk with drift)
returns = np.random.normal(0.0005, 0.02, n_periods)
prices = 100 * np.cumprod(1 + returns)

# Calculate RSI using 14-period lookback
period = 14
delta = np.diff(prices)
gains = np.where(delta > 0, delta, 0)
losses = np.where(delta < 0, -delta, 0)

# Calculate average gains and losses using exponential moving average
avg_gain = np.zeros(len(delta))
avg_loss = np.zeros(len(delta))
avg_gain[period - 1] = np.mean(gains[:period])
avg_loss[period - 1] = np.mean(losses[:period])

for i in range(period, len(delta)):
    avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i]) / period
    avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i]) / period

# Calculate RSI
rs = np.divide(avg_gain, avg_loss, out=np.ones_like(avg_gain), where=avg_loss != 0)
rsi = 100 - (100 / (1 + rs))
rsi = rsi[period - 1 :]  # Valid RSI values start after lookback period
rsi_dates = dates[period:]

# Create DataFrame for plotting
df = pd.DataFrame({"date": rsi_dates, "rsi": rsi})

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Shade overbought zone (70-100)
ax.fill_between(df["date"], 70, 100, alpha=0.15, color="#d62728", label="Overbought zone (>70)")

# Shade oversold zone (0-30)
ax.fill_between(df["date"], 0, 30, alpha=0.15, color="#2ca02c", label="Oversold zone (<30)")

# Plot RSI line
ax.plot(df["date"], df["rsi"], color="#306998", linewidth=3, label="RSI (14-period)")

# Add horizontal reference lines
ax.axhline(y=70, color="#d62728", linestyle="--", linewidth=2, alpha=0.8)
ax.axhline(y=30, color="#2ca02c", linestyle="--", linewidth=2, alpha=0.8)
ax.axhline(y=50, color="#888888", linestyle=":", linewidth=1.5, alpha=0.6)

# Set fixed y-axis from 0 to 100
ax.set_ylim(0, 100)
ax.set_xlim(df["date"].min(), df["date"].max())

# Labels and styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("RSI Value", fontsize=20)
ax.set_title("indicator-rsi · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Add text annotations for threshold levels
ax.text(df["date"].iloc[-1], 72, "Overbought (70)", fontsize=14, color="#d62728", ha="right", va="bottom")
ax.text(df["date"].iloc[-1], 28, "Oversold (30)", fontsize=14, color="#2ca02c", ha="right", va="top")

# Grid and legend
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
