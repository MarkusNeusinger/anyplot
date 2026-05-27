""" anyplot.ai
renko-basic: Basic Renko Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-17
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# imprint semantic anchors
BULLISH = "#009E73"  # green — upward
BEARISH = "#AE3030"  # red — downward

# Generate synthetic price data
np.random.seed(42)
n_points = 200

# Start price and simulate daily returns
start_price = 100
returns = np.random.normal(0.001, 0.02, n_points)
prices = start_price * np.cumprod(1 + returns)

# Renko brick calculation
brick_size = 2.0


def calculate_renko_bricks(close_prices, brick_size):
    """Calculate Renko bricks from close prices."""
    bricks = []
    if len(close_prices) == 0:
        return bricks

    current_price = np.floor(close_prices[0] / brick_size) * brick_size

    for price in close_prices:
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
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Draw bricks
brick_width = 0.8
gap = 0.1

for i, brick in enumerate(bricks):
    color = BULLISH if brick["direction"] > 0 else BEARISH
    edge_color = INK_SOFT

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
ax.set_xlabel("Brick Number", fontsize=20, color=INK)
ax.set_ylabel("Price ($)", fontsize=20, color=INK)
ax.set_title("renko-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Subtle grid for price levels
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Legend with theme-adaptive styling
bullish_patch = mpatches.Patch(color=BULLISH, label="Bullish (Price Up)")
bearish_patch = mpatches.Patch(color=BEARISH, label="Bearish (Price Down)")
leg = ax.legend(handles=[bullish_patch, bearish_patch], loc="upper left", fontsize=16)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
