""" pyplots.ai
ohlc-bar: OHLC Bar Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seaborn style for consistent aesthetics
sns.set_theme(style="whitegrid")

# Generate synthetic OHLC stock data
np.random.seed(42)
n_days = 45

# Create date range (business days)
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Generate realistic price movements
base_price = 150.0
returns = np.random.normal(0.001, 0.02, n_days)
close_prices = base_price * np.cumprod(1 + returns)

# Generate OHLC from close prices
open_prices = np.roll(close_prices, 1)
open_prices[0] = base_price
high_prices = np.maximum(open_prices, close_prices) * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
low_prices = np.minimum(open_prices, close_prices) * (1 - np.abs(np.random.normal(0, 0.01, n_days)))

# Create DataFrame
df = pd.DataFrame({"date": dates, "open": open_prices, "high": high_prices, "low": low_prices, "close": close_prices})

# Add direction column for coloring
df["direction"] = np.where(df["close"] >= df["open"], "up", "down")

# Create figure with seaborn styling
fig, ax = plt.subplots(figsize=(16, 9))

# Define colors - Python blue for up, desaturated red for down
color_up = "#306998"  # Python Blue
color_down = "#C44E52"  # Soft red (colorblind-friendly)

# Draw OHLC bars using seaborn's lineplot for consistent styling
# We'll draw each bar as individual elements
tick_width = 0.4  # Width of open/close ticks

for idx, row in df.iterrows():
    i = df.index.get_loc(idx)
    color = color_up if row["direction"] == "up" else color_down

    # Vertical line from low to high
    ax.vlines(x=i, ymin=row["low"], ymax=row["high"], color=color, linewidth=2)

    # Left tick for open price
    ax.hlines(y=row["open"], xmin=i - tick_width, xmax=i, color=color, linewidth=2)

    # Right tick for close price
    ax.hlines(y=row["close"], xmin=i, xmax=i + tick_width, color=color, linewidth=2)

# Add invisible scatter points for the legend
for label, color in [("Up (Close ≥ Open)", color_up), ("Down (Close < Open)", color_down)]:
    ax.scatter([], [], color=color, s=150, marker="s", label=label)

# Configure x-axis with date labels
tick_positions = np.arange(0, len(df), max(1, len(df) // 8))
tick_labels = [df["date"].iloc[i].strftime("%b %d") for i in tick_positions]
ax.set_xticks(tick_positions)
ax.set_xticklabels(tick_labels, rotation=45, ha="right")

# Style the plot
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.set_title("ohlc-bar · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left", framealpha=0.9)

# Adjust grid
ax.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Set axis limits with padding
ax.set_xlim(-1, len(df))
y_min, y_max = df["low"].min(), df["high"].max()
y_padding = (y_max - y_min) * 0.1
ax.set_ylim(y_min - y_padding, y_max + y_padding)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
