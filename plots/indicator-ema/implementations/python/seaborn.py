""" pyplots.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-11
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Generate realistic stock price data
np.random.seed(42)
n_days = 120

# Create date range for trading days
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Generate price data with realistic stock movement pattern
# Start at $150, add trend and volatility
returns = np.random.normal(0.0008, 0.018, n_days)
price = 150 * np.cumprod(1 + returns)

# Calculate EMAs using pandas ewm
price_series = pd.Series(price)
ema_12 = price_series.ewm(span=12, adjust=False).mean().values
ema_26 = price_series.ewm(span=26, adjust=False).mean().values

# Create DataFrame
df = pd.DataFrame({"date": dates, "close": price, "ema_12": ema_12, "ema_26": ema_26})

# Prepare data for seaborn (long format)
df_long = df.melt(id_vars=["date"], value_vars=["close", "ema_12", "ema_26"], var_name="series", value_name="price")

# Map series names to display labels
series_labels = {"close": "Close Price", "ema_12": "EMA 12", "ema_26": "EMA 26"}
df_long["series_label"] = df_long["series"].map(series_labels)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Define colors: Python Blue for price, Python Yellow for short EMA, distinct color for long EMA
palette = {"Close Price": "#306998", "EMA 12": "#FFD43B", "EMA 26": "#E74C3C"}

# Line widths: price thicker, EMAs thinner
linewidths = {"Close Price": 3.5, "EMA 12": 2.5, "EMA 26": 2.5}

# Plot each series with seaborn
for series_label in ["Close Price", "EMA 12", "EMA 26"]:
    series_data = df_long[df_long["series_label"] == series_label]
    sns.lineplot(
        data=series_data,
        x="date",
        y="price",
        ax=ax,
        color=palette[series_label],
        linewidth=linewidths[series_label],
        label=series_label,
    )

# Find crossover points (where EMA 12 crosses EMA 26)
cross_up = (df["ema_12"].shift(1) < df["ema_26"].shift(1)) & (df["ema_12"] > df["ema_26"])
cross_down = (df["ema_12"].shift(1) > df["ema_26"].shift(1)) & (df["ema_12"] < df["ema_26"])

# Mark crossover points
for idx in df[cross_up].index:
    ax.scatter(df.loc[idx, "date"], df.loc[idx, "ema_12"], color="#27AE60", s=200, zorder=5, marker="^")
for idx in df[cross_down].index:
    ax.scatter(df.loc[idx, "date"], df.loc[idx, "ema_12"], color="#C0392B", s=200, zorder=5, marker="v")

# Styling
ax.set_title("indicator-ema \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price (USD)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

# Legend
ax.legend(fontsize=16, loc="upper left", framealpha=0.9)

# Grid styling
ax.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
