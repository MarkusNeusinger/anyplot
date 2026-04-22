""" pyplots.ai
stock-event-flags: Stock Chart with Event Flags
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-21
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Generate 180 trading days of stock price data
np.random.seed(42)
dates = pd.date_range("2025-01-01", periods=180, freq="B")  # Business days

# Generate realistic stock price data with trend and volatility
initial_price = 150.0
returns = np.random.normal(0.0005, 0.02, size=180)  # Small daily returns
prices = initial_price * np.cumprod(1 + returns)

# Create OHLC-like data
close = prices
high = close * (1 + np.abs(np.random.normal(0, 0.01, size=180)))
low = close * (1 - np.abs(np.random.normal(0, 0.01, size=180)))
open_price = (close + np.random.normal(0, 1, size=180)).clip(low, high)

df = pd.DataFrame({"date": dates, "open": open_price, "high": high, "low": low, "close": close})

# Define events with their dates, types, and labels
events = [
    {"date": "2025-01-28", "type": "earnings", "label": "Q4"},
    {"date": "2025-02-14", "type": "dividend", "label": "0.50"},
    {"date": "2025-03-10", "type": "news", "label": "Launch"},
    {"date": "2025-04-22", "type": "earnings", "label": "Q1"},
    {"date": "2025-05-08", "type": "split", "label": "2:1"},
    {"date": "2025-05-20", "type": "dividend", "label": "0.50"},
    {"date": "2025-06-25", "type": "news", "label": "Interview"},
    {"date": "2025-07-28", "type": "earnings", "label": "Q2"},
    {"date": "2025-08-20", "type": "dividend", "label": "0.55"},
]

events_df = pd.DataFrame(events)
events_df["date"] = pd.to_datetime(events_df["date"])

# Event type styling
event_colors = {
    "earnings": "#306998",  # Python Blue for earnings
    "dividend": "#2E8B57",  # Sea green for dividends
    "split": "#FFD43B",  # Python Yellow for splits
    "news": "#DC143C",  # Crimson for news
}

event_markers = {
    "earnings": "E",  # Chart icon represented by E (Earnings)
    "dividend": "D",  # D for dividends (avoid $ as it triggers math mode)
    "split": "S",  # S for split
    "news": "!",  # Exclamation for news
}

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot price line
ax.plot(df["date"], df["close"], color="#306998", linewidth=2.5, label="Close Price", zorder=2)

# Add a light fill under the price line
ax.fill_between(df["date"], df["close"].min() * 0.95, df["close"], alpha=0.1, color="#306998", zorder=1)

# Determine price range for flag positioning
price_min = df["close"].min()
price_max = df["close"].max()
price_range = price_max - price_min

# Plot event flags with alternating heights to avoid overlap
for idx, event in events_df.iterrows():
    event_date = event["date"]
    event_type = event["type"]
    event_label = event["label"]

    # Find the price at this date
    price_at_date = df.loc[df["date"] == event_date, "close"]
    if len(price_at_date) == 0:
        # Find nearest date
        nearest_idx = np.abs(df["date"] - event_date).argmin()
        price_at_date = df.iloc[nearest_idx]["close"]
    else:
        price_at_date = price_at_date.values[0]

    color = event_colors.get(event_type, "#888888")
    marker_text = event_markers.get(event_type, "?")

    # Alternate flag heights using 3 levels to avoid overlap
    height_level = idx % 3
    flag_y = price_max + price_range * (0.12 + height_level * 0.12)

    # Draw vertical dashed line from flag to price point
    ax.plot(
        [event_date, event_date],
        [price_at_date, flag_y],
        color=color,
        linestyle="--",
        linewidth=1.5,
        alpha=0.7,
        zorder=3,
    )

    # Draw a small circle at the price point
    ax.scatter([event_date], [price_at_date], color=color, s=100, zorder=4, edgecolors="white", linewidth=1.5)

    # Draw flag box with marker
    bbox_props = {"boxstyle": "round,pad=0.4", "facecolor": color, "edgecolor": "white", "linewidth": 2, "alpha": 0.9}
    ax.annotate(
        f"{marker_text} {event_label}",
        xy=(event_date, flag_y),
        fontsize=12,
        fontweight="bold",
        color="white",
        ha="center",
        va="center",
        bbox=bbox_props,
        zorder=5,
    )

# Create legend for event types
legend_patches = [
    mpatches.Patch(color=color, label=event_type.capitalize()) for event_type, color in event_colors.items()
]
ax.legend(handles=legend_patches, loc="upper left", fontsize=14, framealpha=0.9)

# Labels and styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.set_title("stock-event-flags · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", zorder=0)

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

# Set y-axis limits to accommodate flags
ax.set_ylim(price_min * 0.95, price_max + price_range * 0.55)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
