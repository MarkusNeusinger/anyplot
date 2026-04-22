""" pyplots.ai
kagi-basic: Basic Kagi Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


# Generate synthetic stock price data
np.random.seed(42)
n_days = 250
initial_price = 100.0

# Create realistic price movements using geometric brownian motion
daily_returns = np.random.normal(0.0003, 0.015, n_days)
prices = initial_price * np.cumprod(1 + daily_returns)

# Kagi chart construction
reversal_pct = 0.04  # 4% reversal threshold

# Initialize Kagi data structures
kagi_x = [0]
kagi_y = [prices[0]]
kagi_colors = []
kagi_widths = []

current_direction = None  # 'up' or 'down'
current_price = prices[0]
last_high = prices[0]
last_low = prices[0]
is_yang = True  # Start as yang (thick line)
x_pos = 0

for price in prices[1:]:
    reversal_amount = current_price * reversal_pct

    if current_direction is None:
        # Initialize direction based on first significant move
        if price >= current_price + reversal_amount:
            current_direction = "up"
            is_yang = True
            kagi_x.append(x_pos)
            kagi_y.append(price)
            kagi_colors.append("#2E7D32")  # Green for yang
            kagi_widths.append(4)
            current_price = price
            last_high = price
        elif price <= current_price - reversal_amount:
            current_direction = "down"
            is_yang = False
            kagi_x.append(x_pos)
            kagi_y.append(price)
            kagi_colors.append("#C62828")  # Red for yin
            kagi_widths.append(2)
            current_price = price
            last_low = price

    elif current_direction == "up":
        if price > current_price:
            # Continue upward - extend line
            kagi_y[-1] = price
            current_price = price
            # Check if we broke previous high -> become yang
            if price > last_high:
                is_yang = True
                kagi_colors[-1] = "#2E7D32"
                kagi_widths[-1] = 4
                last_high = price
        elif price <= current_price - reversal_amount:
            # Reversal down - draw horizontal then vertical
            x_pos += 1
            # Horizontal shoulder line
            kagi_x.append(x_pos)
            kagi_y.append(current_price)
            kagi_colors.append("#2E7D32" if is_yang else "#C62828")
            kagi_widths.append(4 if is_yang else 2)
            # New vertical down line
            kagi_x.append(x_pos)
            kagi_y.append(price)
            # Check if we broke previous low -> become yin
            if price < last_low:
                is_yang = False
                last_low = price
            kagi_colors.append("#2E7D32" if is_yang else "#C62828")
            kagi_widths.append(4 if is_yang else 2)
            current_direction = "down"
            current_price = price

    elif current_direction == "down":
        if price < current_price:
            # Continue downward - extend line
            kagi_y[-1] = price
            current_price = price
            # Check if we broke previous low -> become yin
            if price < last_low:
                is_yang = False
                kagi_colors[-1] = "#C62828"
                kagi_widths[-1] = 2
                last_low = price
        elif price >= current_price + reversal_amount:
            # Reversal up - draw horizontal then vertical
            x_pos += 1
            # Horizontal waist line
            kagi_x.append(x_pos)
            kagi_y.append(current_price)
            kagi_colors.append("#2E7D32" if is_yang else "#C62828")
            kagi_widths.append(4 if is_yang else 2)
            # New vertical up line
            kagi_x.append(x_pos)
            kagi_y.append(price)
            # Check if we broke previous high -> become yang
            if price > last_high:
                is_yang = True
                last_high = price
            kagi_colors.append("#2E7D32" if is_yang else "#C62828")
            kagi_widths.append(4 if is_yang else 2)
            current_direction = "up"
            current_price = price

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Draw Kagi lines segment by segment
for i in range(len(kagi_colors)):
    ax.plot(
        [kagi_x[i], kagi_x[i + 1]],
        [kagi_y[i], kagi_y[i + 1]],
        color=kagi_colors[i],
        linewidth=kagi_widths[i],
        solid_capstyle="round",
    )

# Create legend handles
legend_elements = [
    Line2D([0], [0], color="#2E7D32", linewidth=4, label="Yang (Bullish)"),
    Line2D([0], [0], color="#C62828", linewidth=2, label="Yin (Bearish)"),
]
ax.legend(handles=legend_elements, fontsize=16, loc="upper left")

# Styling
ax.set_xlabel("Kagi Line Index", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.set_title("kagi-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Add annotation explaining reversal threshold
ax.text(
    0.98,
    0.02,
    f"Reversal threshold: {reversal_pct * 100:.0f}%",
    transform=ax.transAxes,
    fontsize=14,
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
