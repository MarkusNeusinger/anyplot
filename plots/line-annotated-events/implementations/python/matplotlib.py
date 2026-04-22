""" pyplots.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=365, freq="D")
# Generate realistic stock-like price data with trend and volatility
base_price = 150
returns = np.random.randn(365) * 0.015  # Daily returns ~1.5% std
prices = base_price * np.cumprod(1 + returns)

# Event dates and labels (quarterly earnings + major announcements)
events = [
    (pd.Timestamp("2024-02-15"), "Q4 2023\nEarnings"),
    (pd.Timestamp("2024-05-10"), "Q1 2024\nEarnings"),
    (pd.Timestamp("2024-07-22"), "Product\nLaunch"),
    (pd.Timestamp("2024-08-08"), "Q2 2024\nEarnings"),
    (pd.Timestamp("2024-11-14"), "Q3 2024\nEarnings"),
]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Main line
ax.plot(dates, prices, linewidth=2.5, color="#306998", label="Stock Price", zorder=2)

# Event markers with alternating heights
event_colors = "#FFD43B"
heights = [0.85, 0.70, 0.85, 0.70, 0.85]  # Alternating heights to avoid overlap

for i, (event_date, event_label) in enumerate(events):
    # Vertical line
    ax.axvline(x=event_date, color=event_colors, linestyle="--", linewidth=2, alpha=0.8, zorder=1)
    # Text annotation with alternating heights
    y_pos = ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * heights[i]
    ax.annotate(
        event_label,
        xy=(event_date, prices[dates.get_loc(event_date)]),
        xytext=(event_date, y_pos),
        fontsize=14,
        ha="center",
        va="bottom",
        color="#333333",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#FFD43B", "alpha": 0.9},
        arrowprops={"arrowstyle": "->", "color": "#FFD43B", "lw": 1.5},
    )

# Add event marker to legend
ax.axvline(x=dates[0], color=event_colors, linestyle="--", linewidth=2, alpha=0, label="Event Marker")

# Styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price (USD)", fontsize=20)
ax.set_title("line-annotated-events · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="upper left")

# Format x-axis for better date readability
fig.autofmt_xdate(rotation=30)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
