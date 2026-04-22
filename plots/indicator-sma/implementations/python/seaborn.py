""" pyplots.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-11
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Generate realistic stock price data
np.random.seed(42)
n_days = 300

# Create date range (trading days)
dates = pd.date_range(start="2025-01-01", periods=n_days, freq="B")

# Generate price data with trend and volatility
# Start at $100, with drift and random walk
returns = np.random.normal(0.0005, 0.015, n_days)
prices = 100 * np.cumprod(1 + returns)

# Add some trend structure
trend = np.linspace(0, 20, n_days)
prices = prices + trend * 0.3

# Create DataFrame
df = pd.DataFrame({"date": dates, "close": prices})

# Calculate SMAs
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Prepare data for seaborn (long format)
df_long = pd.melt(
    df, id_vars=["date"], value_vars=["close", "sma_20", "sma_50", "sma_200"], var_name="series", value_name="price"
)

# Set up style
sns.set_style("whitegrid")

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Define colors - Python Blue for close, distinct colors for SMAs
color_palette = {
    "close": "#306998",  # Python Blue
    "sma_20": "#FFD43B",  # Python Yellow
    "sma_50": "#E74C3C",  # Red
    "sma_200": "#2ECC71",  # Green
}

# Plot each series with seaborn
for series_name, color in color_palette.items():
    series_data = df_long[df_long["series"] == series_name]
    linewidth = 2.5 if series_name == "close" else 2.0
    alpha = 1.0 if series_name == "close" else 0.85
    sns.lineplot(
        data=series_data,
        x="date",
        y="price",
        color=color,
        linewidth=linewidth,
        alpha=alpha,
        label=series_name.upper().replace("_", " ") if series_name != "close" else "Close Price",
        ax=ax,
    )

# Style the plot
ax.set_title("indicator-sma · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

# Configure legend
ax.legend(fontsize=16, loc="upper left", framealpha=0.95)

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

# Subtle grid
ax.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
