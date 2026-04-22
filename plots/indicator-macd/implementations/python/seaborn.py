""" pyplots.ai
indicator-macd: MACD Technical Indicator Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Generate synthetic stock price data for MACD calculation
np.random.seed(42)
n_days = 120
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")

# Simulate stock price movement with trend and volatility
returns = np.random.normal(0.001, 0.015, n_days)
price = 100 * np.exp(np.cumsum(returns))

# Calculate Exponential Moving Averages
df = pd.DataFrame({"date": dates, "close": price})
df["ema12"] = df["close"].ewm(span=12, adjust=False).mean()
df["ema26"] = df["close"].ewm(span=26, adjust=False).mean()

# Calculate MACD components
df["macd"] = df["ema12"] - df["ema26"]
df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
df["histogram"] = df["macd"] - df["signal"]

# Drop initial periods where EMAs are not stable
df = df.iloc[33:].reset_index(drop=True)

# Prepare histogram colors
df["hist_color"] = np.where(df["histogram"] >= 0, "#2ca02c", "#d62728")

# Create figure with proper sizing for 4800x2700 at 300 DPI
fig, ax = plt.subplots(figsize=(16, 9))

# Plot histogram as bars
bar_width = 0.8
for _, row in df.iterrows():
    ax.bar(row["date"], row["histogram"], width=bar_width, color=row["hist_color"], alpha=0.7)

# Plot MACD line
sns.lineplot(data=df, x="date", y="macd", ax=ax, color="#306998", linewidth=3, label="MACD (12, 26)")

# Plot Signal line
sns.lineplot(data=df, x="date", y="signal", ax=ax, color="#FFD43B", linewidth=3, label="Signal (9)")

# Add zero reference line
ax.axhline(y=0, color="gray", linestyle="--", linewidth=1.5, alpha=0.7)

# Style the plot
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("MACD Value", fontsize=20)
ax.set_title("indicator-macd · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")

# Rotate x-axis labels for better readability
plt.xticks(rotation=45, ha="right")

# Add annotation for MACD parameters
ax.annotate(
    "MACD Parameters: 12, 26, 9",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    fontsize=14,
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "gray", "alpha": 0.8},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
