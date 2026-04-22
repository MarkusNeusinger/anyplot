""" pyplots.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-11
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Generate realistic stock price data with EMAs
np.random.seed(42)
n_days = 120

# Generate price data using random walk
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")  # Business days
returns = np.random.normal(0.0005, 0.02, n_days)  # Daily returns
price = 150 * np.cumprod(1 + returns)  # Starting price ~$150

# Create DataFrame
df = pd.DataFrame({"date": dates, "close": price})

# Calculate EMAs using pandas ewm (exponential weighted moving average)
df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Price line (most prominent)
ax.plot(df["date"], df["close"], linewidth=2.5, color="#333333", label="Price", alpha=0.9)

# EMA lines (slightly thinner as per spec)
ax.plot(df["date"], df["ema_12"], linewidth=2, color="#306998", label="EMA 12", alpha=0.85)
ax.plot(df["date"], df["ema_26"], linewidth=2, color="#FFD43B", label="EMA 26", alpha=0.85)

# Find and highlight crossover points
crossover_idx = np.where(np.diff(np.sign(df["ema_12"].values - df["ema_26"].values)))[0]
for idx in crossover_idx:
    ax.scatter(
        df["date"].iloc[idx], df["ema_12"].iloc[idx], s=200, color="#E74C3C", zorder=5, edgecolors="white", linewidths=2
    )

# Labels and styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.set_title("indicator-ema · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
