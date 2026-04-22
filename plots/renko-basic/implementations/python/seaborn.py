""" pyplots.ai
renko-basic: Basic Renko Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 68/100 | Created: 2026-01-08
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Rectangle


# Set seaborn style
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.2)

# Generate synthetic stock price data
np.random.seed(42)
n_days = 250
dates = pd.date_range("2025-01-01", periods=n_days, freq="D")

# Simulate price movement with random walk
returns = np.random.normal(0.0005, 0.015, n_days)
prices = 100 * np.cumprod(1 + returns)

df = pd.DataFrame({"date": dates, "close": prices})

# Renko brick calculation
brick_size = 2.0  # $2 per brick
bricks = []

# Start from first price
current_price = df["close"].iloc[0]
brick_high = np.floor(current_price / brick_size) * brick_size
brick_low = brick_high

for price in df["close"]:
    # Check for upward bricks
    while price >= brick_high + brick_size:
        brick_high += brick_size
        brick_low = brick_high - brick_size
        bricks.append({"direction": "up", "open": brick_low, "close": brick_high})

    # Check for downward bricks
    while price <= brick_low - brick_size:
        brick_low -= brick_size
        brick_high = brick_low + brick_size
        bricks.append({"direction": "down", "open": brick_high, "close": brick_low})

renko_df = pd.DataFrame(bricks)

# Colorblind-accessible colors (blue/orange scheme instead of red/green)
bullish_color = "#1976D2"  # Blue for up bricks (colorblind-safe)
bearish_color = "#E65100"  # Orange for down bricks (colorblind-safe)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Gap ratio for small separation between bricks
gap_ratio = 0.08
brick_width = 1.0 - gap_ratio

# Draw bricks in proper stair-step pattern
# Each brick is positioned at (x, bottom) with height = brick_size
# The key for Renko: next brick starts at the SAME y-level where previous ended
bullish_patches = []
bearish_patches = []

for idx, row in renko_df.iterrows():
    bottom = min(row["open"], row["close"])
    x_pos = idx + gap_ratio / 2  # Center the brick with gap

    rect = Rectangle((x_pos, bottom), brick_width, brick_size, linewidth=1.5, edgecolor="white")

    if row["direction"] == "up":
        rect.set_facecolor(bullish_color)
        bullish_patches.append(rect)
    else:
        rect.set_facecolor(bearish_color)
        bearish_patches.append(rect)

    ax.add_patch(rect)

# Add legend handles with updated labels
legend_handles = [
    Rectangle((0, 0), 1, 1, facecolor=bullish_color, edgecolor="white", label="Bullish (Up)"),
    Rectangle((0, 0), 1, 1, facecolor=bearish_color, edgecolor="white", label="Bearish (Down)"),
]

# Set axis limits with padding
price_min = renko_df[["open", "close"]].min().min() - brick_size
price_max = renko_df[["open", "close"]].max().max() + brick_size
ax.set_ylim(price_min, price_max)
ax.set_xlim(-0.5, len(renko_df) + 0.5)

# Labels and styling - more descriptive axis labels
ax.set_xlabel("Brick Number", fontsize=20)
ax.set_ylabel("Stock Price (USD)", fontsize=20)
ax.set_title("renko-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.tick_params(axis="both", labelsize=16)

# Add legend positioned outside plot area to avoid data overlap
ax.legend(handles=legend_handles, fontsize=16, loc="upper right", framealpha=0.9)

# Add subtle grid on y-axis only
ax.grid(True, alpha=0.3, linestyle="--", axis="y")
ax.set_axisbelow(True)

# Simplify x-axis ticks for cleaner look
tick_step = max(1, len(renko_df) // 10)
ax.set_xticks(range(0, len(renko_df), tick_step))

# Add annotation about brick size
ax.annotate(
    f"Brick Size: ${brick_size:.0f}",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    fontsize=14,
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "gray", "alpha": 0.8},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
