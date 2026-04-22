""" pyplots.ai
point-and-figure-basic: Point and Figure Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


# Generate synthetic price data simulating stock price movements
np.random.seed(42)
n_days = 300

# Starting price and random walk with trend
base_price = 100
returns = np.random.normal(0.001, 0.02, n_days)  # Daily returns
close = base_price * np.cumprod(1 + returns)

# Generate high/low around close
volatility = np.abs(np.random.normal(0, 0.01, n_days))
high = close * (1 + volatility)
low = close * (1 - volatility)

# P&F chart parameters
box_size = 2.0  # Price increment per box
reversal = 3  # Boxes needed to reverse

# Build P&F columns from price data
columns = []  # Each column: {'type': 'X' or 'O', 'start': price, 'end': price}
current_col = None
current_price = None

for i in range(len(close)):
    price = close[i]

    if current_col is None:
        # Initialize first column based on price direction
        current_col = {
            "type": "X",
            "start": np.floor(price / box_size) * box_size,
            "end": np.floor(price / box_size) * box_size,
        }
        current_price = current_col["end"]
        continue

    if current_col["type"] == "X":
        # In an X (up) column
        new_high = np.floor(price / box_size) * box_size
        if new_high > current_col["end"]:
            # Extend column up
            current_col["end"] = new_high
            current_price = new_high
        elif price <= current_price - reversal * box_size:
            # Reversal to O column
            columns.append(current_col.copy())
            new_start = current_col["end"] - box_size  # Start one box below
            new_end = np.ceil(price / box_size) * box_size
            current_col = {"type": "O", "start": new_start, "end": new_end}
            current_price = new_end
    else:
        # In an O (down) column
        new_low = np.ceil(price / box_size) * box_size
        if new_low < current_col["end"]:
            # Extend column down
            current_col["end"] = new_low
            current_price = new_low
        elif price >= current_price + reversal * box_size:
            # Reversal to X column
            columns.append(current_col.copy())
            new_start = current_col["end"] + box_size  # Start one box above
            new_end = np.floor(price / box_size) * box_size
            current_col = {"type": "X", "start": new_start, "end": new_end}
            current_price = new_end

# Append last column
if current_col is not None:
    columns.append(current_col)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Define colors
x_color = "#306998"  # Python Blue for bullish
o_color = "#D62728"  # Red for bearish

# Plot each column
for col_idx, col in enumerate(columns):
    if col["type"] == "X":
        # X column goes from start to end (upward)
        start = min(col["start"], col["end"])
        end = max(col["start"], col["end"])
        boxes = np.arange(start, end + box_size / 2, box_size)
        for box_price in boxes:
            ax.text(col_idx, box_price, "X", fontsize=14, fontweight="bold", ha="center", va="center", color=x_color)
    else:
        # O column goes from start to end (downward)
        start = max(col["start"], col["end"])
        end = min(col["start"], col["end"])
        boxes = np.arange(end, start + box_size / 2, box_size)
        for box_price in boxes:
            ax.text(col_idx, box_price, "O", fontsize=14, fontweight="bold", ha="center", va="center", color=o_color)

# Calculate y-axis limits from the data
all_prices = []
for col in columns:
    all_prices.extend([col["start"], col["end"]])
y_min = min(all_prices) - 2 * box_size
y_max = max(all_prices) + 2 * box_size

# Configure axes
ax.set_xlim(-0.5, len(columns) - 0.5)
ax.set_ylim(y_min, y_max)

# Grid at box size intervals
ax.set_yticks(
    np.arange(np.floor(y_min / box_size) * box_size, np.ceil(y_max / box_size) * box_size + box_size, box_size)
)
ax.grid(True, alpha=0.3, linestyle="-", which="both")

# Labels and title
ax.set_xlabel("Column (Reversal Number)", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.set_title("point-and-figure-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Add legend
legend_elements = [
    Line2D(
        [0],
        [0],
        marker="$X$",
        color="w",
        markerfacecolor=x_color,
        markersize=20,
        label="Rising (X)",
        markeredgecolor=x_color,
    ),
    Line2D(
        [0],
        [0],
        marker="$O$",
        color="w",
        markerfacecolor=o_color,
        markersize=20,
        label="Falling (O)",
        markeredgecolor=o_color,
    ),
]
ax.legend(handles=legend_elements, fontsize=16, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
