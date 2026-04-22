""" pyplots.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch


# Data - Generate realistic 60 trading days of OHLC data with volume
np.random.seed(42)
n_days = 60
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")  # Business days

# Generate price path with realistic movement
base_price = 150.0
returns = np.random.normal(0.001, 0.02, n_days)
prices = base_price * np.cumprod(1 + returns)

# Create OHLC data
opens = np.zeros(n_days)
highs = np.zeros(n_days)
lows = np.zeros(n_days)
closes = np.zeros(n_days)

opens[0] = base_price
closes[0] = prices[0]
for i in range(1, n_days):
    opens[i] = closes[i - 1] * (1 + np.random.normal(0, 0.005))
    closes[i] = prices[i]

# High/low based on open/close with some variation
for i in range(n_days):
    oc_max = max(opens[i], closes[i])
    oc_min = min(opens[i], closes[i])
    highs[i] = oc_max + np.random.uniform(0.5, 2.0)
    lows[i] = oc_min - np.random.uniform(0.5, 2.0)

# Volume with higher volume on big moves
base_volume = 5_000_000
volume_multiplier = 1 + np.abs(closes - opens) / opens * 20
volumes = base_volume * volume_multiplier * np.random.uniform(0.7, 1.3, n_days)
volumes = volumes.astype(int)

# Colors for up/down days
up_color = "#306998"  # Python Blue for up
down_color = "#FFD43B"  # Python Yellow for down
is_up = closes >= opens

# Create figure with two subplots sharing x-axis (75% price, 25% volume)
fig, (ax_price, ax_volume) = plt.subplots(2, 1, figsize=(16, 9), gridspec_kw={"height_ratios": [3, 1]}, sharex=True)

# Candlestick chart - Price pane
candle_width = 0.6
for i in range(n_days):
    color = up_color if is_up[i] else down_color
    # Draw wick (high-low line)
    ax_price.plot([dates[i], dates[i]], [lows[i], highs[i]], color=color, linewidth=1.5, solid_capstyle="round")
    # Draw body (open-close rectangle)
    body_bottom = min(opens[i], closes[i])
    body_height = abs(closes[i] - opens[i])
    ax_price.bar(
        dates[i], body_height, width=candle_width, bottom=body_bottom, color=color, edgecolor=color, linewidth=0.5
    )

# Volume bars with matching colors
for i in range(n_days):
    color = up_color if is_up[i] else down_color
    ax_volume.bar(dates[i], volumes[i], width=candle_width, color=color, alpha=0.8)

# Price pane styling
ax_price.set_ylabel("Price ($)", fontsize=20)
ax_price.tick_params(axis="both", labelsize=16)
ax_price.grid(True, alpha=0.3, linestyle="--")
ax_price.set_title("candlestick-volume · matplotlib · pyplots.ai", fontsize=24, pad=15)

# Add legend
legend_elements = [
    Patch(facecolor=up_color, label="Up (Close ≥ Open)"),
    Patch(facecolor=down_color, label="Down (Close < Open)"),
]
ax_price.legend(handles=legend_elements, loc="upper left", fontsize=14)

# Volume pane styling
ax_volume.set_xlabel("Date", fontsize=20)
ax_volume.set_ylabel("Volume", fontsize=20)
ax_volume.tick_params(axis="both", labelsize=16)
ax_volume.grid(True, alpha=0.3, linestyle="--")

# Format y-axis for volume (in millions)
ax_volume.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x / 1e6:.1f}M"))

# Format x-axis dates
ax_volume.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
ax_volume.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
plt.setp(ax_volume.xaxis.get_majorticklabels(), rotation=45, ha="right")

# Ensure y-axis starts at 0 for volume
ax_volume.set_ylim(bottom=0)

# Add crosshair cursor via spines styling (visual alignment between panes)
for ax in [ax_price, ax_volume]:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
