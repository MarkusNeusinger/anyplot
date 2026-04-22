""" pyplots.ai
renko-basic: Basic Renko Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Generate synthetic price data
np.random.seed(42)
n_points = 200

# Start price and simulate daily returns
start_price = 100
returns = np.random.normal(0.001, 0.02, n_points)  # Daily returns with slight upward drift
prices = start_price * np.cumprod(1 + returns)

# Renko brick calculation
brick_size = 2.0  # Fixed $2 brick size


def calculate_renko_bricks(close_prices, brick_size):
    """Calculate Renko bricks from close prices."""
    bricks = []
    if len(close_prices) == 0:
        return bricks

    # Initialize with first price, rounded to brick size
    current_price = np.floor(close_prices[0] / brick_size) * brick_size

    for price in close_prices:
        # Calculate how many bricks to draw
        diff = price - current_price
        num_bricks = int(abs(diff) // brick_size)

        if num_bricks > 0:
            direction = 1 if diff > 0 else -1
            for _ in range(num_bricks):
                brick_bottom = current_price if direction > 0 else current_price - brick_size
                bricks.append({"bottom": brick_bottom, "top": brick_bottom + brick_size, "direction": direction})
                current_price += direction * brick_size

    return bricks


# Calculate Renko bricks
bricks = calculate_renko_bricks(prices, brick_size)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Colors
bullish_color = "#22c55e"  # Green for upward
bearish_color = "#ef4444"  # Red for downward

# Draw bricks
brick_width = 0.8
gap = 0.1

for i, brick in enumerate(bricks):
    color = bullish_color if brick["direction"] > 0 else bearish_color
    edge_color = "#166534" if brick["direction"] > 0 else "#991b1b"

    # Draw brick as rectangle
    rect = mpatches.Rectangle(
        (i + gap / 2, brick["bottom"]),
        brick_width,
        brick_size,
        linewidth=1.5,
        edgecolor=edge_color,
        facecolor=color,
        alpha=0.9,
    )
    ax.add_patch(rect)

# Set axis limits
ax.set_xlim(-1, len(bricks) + 1)
all_prices = [b["bottom"] for b in bricks] + [b["top"] for b in bricks]
ax.set_ylim(min(all_prices) - brick_size, max(all_prices) + brick_size)

# Labels and styling
ax.set_xlabel("Brick Number", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.set_title("renko-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Subtle grid for price levels
ax.grid(True, alpha=0.3, linestyle="--", axis="y")
ax.set_axisbelow(True)

# Legend
bullish_patch = mpatches.Patch(color=bullish_color, label="Bullish (Price Up)")
bearish_patch = mpatches.Patch(color=bearish_color, label="Bearish (Price Down)")
ax.legend(handles=[bullish_patch, bearish_patch], loc="upper left", fontsize=16)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
