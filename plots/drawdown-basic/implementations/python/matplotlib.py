""" pyplots.ai
drawdown-basic: Drawdown Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


# Data - Simulate 2 years of daily portfolio values with distinct drawdown/recovery cycles
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=500, freq="B")  # Business days
n_points = len(dates)

# Build price series with explicit drawdown and recovery phases
prices = [10000]
trend = 0.0008  # Daily upward trend

for i in range(1, n_points):
    # Different market regimes
    if 50 <= i < 85:  # Drawdown 1: ~15% drop
        drift = -0.005
    elif 85 <= i < 130:  # Recovery 1
        drift = 0.004
    elif 180 <= i < 230:  # Drawdown 2: ~25% drop (max drawdown)
        drift = -0.006
    elif 230 <= i < 320:  # Recovery 2
        drift = 0.003
    elif 350 <= i < 380:  # Drawdown 3: ~12% drop
        drift = -0.004
    elif 380 <= i < 430:  # Recovery 3
        drift = 0.003
    elif 450 <= i < 470:  # Drawdown 4: ~8% drop
        drift = -0.004
    else:  # Normal periods with slight growth
        drift = trend

    noise = np.random.normal(0, 0.008)
    new_price = prices[-1] * (1 + drift + noise)
    prices.append(new_price)

portfolio_value = np.array(prices)

# Calculate drawdown
running_max = np.maximum.accumulate(portfolio_value)
drawdown = (portfolio_value - running_max) / running_max * 100

# Find maximum drawdown point
max_dd_idx = np.argmin(drawdown)
max_dd_value = drawdown[max_dd_idx]
max_dd_date = dates[max_dd_idx]

# Find start of max drawdown period (last peak before max drawdown)
peak_mask = portfolio_value[:max_dd_idx] == running_max[:max_dd_idx]
if peak_mask.any():
    peak_before_max_dd = np.where(peak_mask)[0][-1]
else:
    peak_before_max_dd = 0
peak_date = dates[peak_before_max_dd]

# Find recovery point after max drawdown (where drawdown returns to 0)
recovery_after_max = None
for i in range(max_dd_idx + 1, len(drawdown)):
    if drawdown[i] >= -0.01:  # Close to 0
        recovery_after_max = dates[i]
        break

# Calculate recovery duration
if recovery_after_max is not None:
    recovery_days = (recovery_after_max - max_dd_date).days
else:
    recovery_days = "N/A"

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Fill area below zero (drawdown region)
ax.fill_between(dates, drawdown, 0, where=(drawdown < 0), color="#D9534F", alpha=0.4, label="Drawdown")

# Drawdown line
ax.plot(dates, drawdown, color="#D9534F", linewidth=2.5)

# Zero baseline
ax.axhline(y=0, color="#306998", linewidth=2, linestyle="-", alpha=0.8)

# Mark maximum drawdown point
ax.scatter([max_dd_date], [max_dd_value], color="#8B0000", s=200, zorder=5, edgecolors="white", linewidths=2)
ax.annotate(
    f"Max DD: {max_dd_value:.1f}%",
    xy=(max_dd_date, max_dd_value),
    xytext=(40, 20),
    textcoords="offset points",
    fontsize=14,
    fontweight="bold",
    color="#8B0000",
    arrowprops={"arrowstyle": "->", "color": "#8B0000", "lw": 2},
)

# Mark recovery points (where drawdown returns to 0 after being negative)
recovery_indices = []
for i in range(1, len(drawdown)):
    if drawdown[i] >= -0.01 and drawdown[i - 1] < -0.5:  # Recovery to ~0%
        recovery_indices.append(i)

for idx in recovery_indices[:6]:  # Limit to first 6 recoveries for clarity
    ax.scatter([dates[idx]], [0], color="#306998", s=120, marker="^", zorder=5)

# Add key statistics box
stats_text = (
    f"Max Drawdown: {max_dd_value:.1f}%\n"
    f"Max DD Date: {max_dd_date.strftime('%Y-%m-%d')}\n"
    f"Peak to Trough: {(max_dd_date - peak_date).days} days\n"
    f"Recovery: {recovery_days} days"
)
props = {"boxstyle": "round,pad=0.5", "facecolor": "white", "alpha": 0.9, "edgecolor": "#306998"}
ax.text(0.02, 0.02, stats_text, transform=ax.transAxes, fontsize=14, verticalalignment="bottom", bbox=props)

# Labels and styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Drawdown (%)", fontsize=20)
ax.set_title("drawdown-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Format y-axis to show percentage values clearly
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))

# Set y-axis limits to show full drawdown range with some padding
ax.set_ylim(min(drawdown) * 1.15, 5)

# Legend with recovery marker explanation
custom_handles = [
    plt.Rectangle((0, 0), 1, 1, fc="#D9534F", alpha=0.4, label="Drawdown"),
    Line2D([0], [0], marker="^", color="w", markerfacecolor="#306998", markersize=12, label="Recovery (New High)"),
]
ax.legend(handles=custom_handles, loc="upper right", fontsize=16)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
