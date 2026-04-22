""" pyplots.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Generate realistic stock price data with Bollinger Bands
np.random.seed(42)

# Generate 120 trading days of price data
n_days = 120
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Simulate price movement with trend and volatility
returns = np.random.normal(0.0005, 0.015, n_days)
price_base = 150
prices = price_base * np.cumprod(1 + returns)

# Add some volatility clustering (higher volatility periods)
volatility_boost = np.zeros(n_days)
volatility_boost[30:50] = np.random.normal(0, 0.01, 20)  # High volatility period
volatility_boost[80:95] = np.random.normal(0, 0.008, 15)  # Another volatile period
prices = prices * (1 + volatility_boost)

# Calculate Bollinger Bands (20-period SMA, 2 standard deviations)
window = 20
close = pd.Series(prices)
sma = close.rolling(window=window).mean()
std = close.rolling(window=window).std()
upper_band = sma + 2 * std
lower_band = sma - 2 * std

# Create DataFrame
df = pd.DataFrame({"date": dates, "close": close, "sma": sma, "upper_band": upper_band, "lower_band": lower_band})

# Drop NaN values from rolling calculation
df = df.dropna().reset_index(drop=True)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Plot Bollinger Bands fill between upper and lower
ax.fill_between(
    df["date"], df["lower_band"], df["upper_band"], alpha=0.2, color="#306998", label="Bollinger Band Range"
)

# Plot upper band
sns.lineplot(
    data=df, x="date", y="upper_band", ax=ax, color="#306998", linewidth=2, alpha=0.8, label="Upper Band (+2σ)"
)

# Plot lower band
sns.lineplot(
    data=df, x="date", y="lower_band", ax=ax, color="#306998", linewidth=2, alpha=0.8, label="Lower Band (-2σ)"
)

# Plot SMA (middle band) - dashed line
sns.lineplot(data=df, x="date", y="sma", ax=ax, color="#FFD43B", linewidth=2.5, linestyle="--", label="20-Day SMA")

# Plot close price - prominent line
sns.lineplot(data=df, x="date", y="close", ax=ax, color="#1a1a2e", linewidth=3, label="Close Price")

# Styling
ax.set_title("indicator-bollinger · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

# Legend
ax.legend(fontsize=14, loc="upper left", framealpha=0.9)

# Grid
ax.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
