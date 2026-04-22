""" pyplots.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Stock-like data with price, volume, and technical indicator
np.random.seed(42)
n_points = 200
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

# Price: random walk with drift
price = 100 + np.cumsum(np.random.randn(n_points) * 2 + 0.05)

# Volume: correlated with absolute price changes
volume = np.abs(np.diff(price, prepend=price[0])) * 1e6 + np.random.uniform(0.5e6, 2e6, n_points)

# RSI-like indicator: oscillating between 30-70 with occasional extremes
rsi = 50 + np.cumsum(np.random.randn(n_points) * 3)
rsi = np.clip(rsi, 10, 90)
rsi = 30 + (rsi - rsi.min()) / (rsi.max() - rsi.min()) * 40  # Normalize to 30-70 range

# Create figure with 3 vertically stacked subplots sharing x-axis
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
fig.subplots_adjust(hspace=0.05)

# Chart 1: Price
ax1.plot(dates, price, color="#306998", linewidth=2.5, label="Price")
ax1.fill_between(dates, price, alpha=0.1, color="#306998")
ax1.set_ylabel("Price ($)", fontsize=18)
ax1.legend(fontsize=14, loc="upper left")
ax1.grid(True, alpha=0.3, linestyle="--")
ax1.tick_params(axis="y", labelsize=14)
ax1.set_title("dashboard-synchronized-crosshair · matplotlib · pyplots.ai", fontsize=22, pad=15)

# Chart 2: Volume
colors = ["#4CAF50" if price[i] >= price[max(0, i - 1)] else "#F44336" for i in range(n_points)]
ax2.bar(dates, volume / 1e6, color=colors, alpha=0.7, width=1.5, label="Volume")
ax2.set_ylabel("Volume (M)", fontsize=18)
ax2.legend(fontsize=14, loc="upper left")
ax2.grid(True, alpha=0.3, linestyle="--")
ax2.tick_params(axis="y", labelsize=14)

# Chart 3: RSI indicator
ax3.plot(dates, rsi, color="#FFD43B", linewidth=2.5, label="RSI")
ax3.axhline(y=70, color="#F44336", linestyle="--", linewidth=1.5, alpha=0.7, label="Overbought (70)")
ax3.axhline(y=30, color="#4CAF50", linestyle="--", linewidth=1.5, alpha=0.7, label="Oversold (30)")
ax3.fill_between(dates, 30, 70, alpha=0.1, color="#888888")
ax3.set_ylabel("RSI", fontsize=18)
ax3.set_ylim(20, 80)
ax3.legend(fontsize=12, loc="upper left", ncol=3)
ax3.grid(True, alpha=0.3, linestyle="--")
ax3.tick_params(axis="both", labelsize=14)
ax3.set_xlabel("Date", fontsize=18)

# Add synchronized crosshair demonstration (static annotation for matplotlib)
# Demonstrate crosshair at a specific point
crosshair_idx = 120
crosshair_date = dates[crosshair_idx]
crosshair_price = price[crosshair_idx]
crosshair_vol = volume[crosshair_idx] / 1e6
crosshair_rsi = rsi[crosshair_idx]

# Draw vertical crosshair line across all charts
for ax in [ax1, ax2, ax3]:
    ax.axvline(x=crosshair_date, color="#666666", linestyle="-", linewidth=2, alpha=0.7)

# Add value annotations at crosshair position
ax1.annotate(
    f"${crosshair_price:.2f}",
    xy=(crosshair_date, crosshair_price),
    xytext=(10, 0),
    textcoords="offset points",
    fontsize=14,
    fontweight="bold",
    color="#306998",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#306998", "alpha": 0.9},
)
ax1.scatter([crosshair_date], [crosshair_price], color="#306998", s=100, zorder=5)

ax2.annotate(
    f"{crosshair_vol:.2f}M",
    xy=(crosshair_date, crosshair_vol),
    xytext=(10, 0),
    textcoords="offset points",
    fontsize=14,
    fontweight="bold",
    color="#333333",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#666666", "alpha": 0.9},
)

ax3.annotate(
    f"RSI: {crosshair_rsi:.1f}",
    xy=(crosshair_date, crosshair_rsi),
    xytext=(10, 0),
    textcoords="offset points",
    fontsize=14,
    fontweight="bold",
    color="#FFD43B",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#FFD43B", "alpha": 0.9},
)
ax3.scatter([crosshair_date], [crosshair_rsi], color="#FFD43B", s=100, zorder=5, edgecolor="#333333")

# Add note about synchronized crosshair behavior
fig.text(
    0.5,
    0.01,
    "Note: Vertical crosshair synchronized across all charts (static demonstration for matplotlib)",
    ha="center",
    fontsize=12,
    style="italic",
    color="#666666",
)

plt.tight_layout()
plt.subplots_adjust(bottom=0.06)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
