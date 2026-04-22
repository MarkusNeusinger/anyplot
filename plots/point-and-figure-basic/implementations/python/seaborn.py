""" pyplots.ai
point-and-figure-basic: Point and Figure Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Generate synthetic stock price data
np.random.seed(42)
n_days = 300
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")

# Create realistic price movement with trend changes
base_price = 100
returns = np.random.normal(0.001, 0.02, n_days)
# Add some trending periods
returns[50:100] += 0.005  # Uptrend
returns[150:200] -= 0.005  # Downtrend
returns[250:280] += 0.004  # Another uptrend

prices = base_price * np.exp(np.cumsum(returns))

# Create OHLC data
high = prices * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
low = prices * (1 - np.abs(np.random.normal(0, 0.01, n_days)))
close = prices

df = pd.DataFrame({"date": dates, "high": high, "low": low, "close": close})

# Point and Figure calculation parameters
box_size = 2.0  # $2 per box
reversal = 3  # 3-box reversal


# Calculate Point and Figure columns
def calculate_pnf(close_prices, box_size, reversal):
    """Calculate P&F chart data from close prices."""
    columns = []  # List of (column_index, box_values, direction)
    current_direction = None  # 'X' for up, 'O' for down
    current_col_boxes = []
    col_index = 0

    # Round first price to nearest box
    first_box = round(close_prices.iloc[0] / box_size) * box_size

    for price in close_prices:
        rounded_price = round(price / box_size) * box_size

        if current_direction is None:
            # Initialize first column
            current_col_boxes = [first_box]
            if rounded_price > first_box:
                current_direction = "X"
                while current_col_boxes[-1] + box_size <= rounded_price:
                    current_col_boxes.append(current_col_boxes[-1] + box_size)
            elif rounded_price < first_box:
                current_direction = "O"
                while current_col_boxes[-1] - box_size >= rounded_price:
                    current_col_boxes.append(current_col_boxes[-1] - box_size)
            continue

        if current_direction == "X":
            # In an X column (rising)
            top_box = max(current_col_boxes)
            if rounded_price >= top_box + box_size:
                # Continue up
                while current_col_boxes[-1] + box_size <= rounded_price:
                    current_col_boxes.append(current_col_boxes[-1] + box_size)
            elif rounded_price <= top_box - reversal * box_size:
                # Reversal to O column
                columns.append((col_index, current_col_boxes.copy(), "X"))
                col_index += 1
                start_box = top_box - box_size
                current_col_boxes = [start_box]
                current_direction = "O"
                while current_col_boxes[-1] - box_size >= rounded_price:
                    current_col_boxes.append(current_col_boxes[-1] - box_size)
        else:
            # In an O column (falling)
            bottom_box = min(current_col_boxes)
            if rounded_price <= bottom_box - box_size:
                # Continue down
                while current_col_boxes[-1] - box_size >= rounded_price:
                    current_col_boxes.append(current_col_boxes[-1] - box_size)
            elif rounded_price >= bottom_box + reversal * box_size:
                # Reversal to X column
                columns.append((col_index, current_col_boxes.copy(), "O"))
                col_index += 1
                start_box = bottom_box + box_size
                current_col_boxes = [start_box]
                current_direction = "X"
                while current_col_boxes[-1] + box_size <= rounded_price:
                    current_col_boxes.append(current_col_boxes[-1] + box_size)

    # Add final column
    if current_col_boxes:
        columns.append((col_index, current_col_boxes, current_direction))

    return columns


pnf_columns = calculate_pnf(df["close"], box_size, reversal)

# Prepare data for seaborn scatter plot
plot_data = []
for col_idx, boxes, direction in pnf_columns:
    for box in boxes:
        plot_data.append(
            {"column": col_idx, "price": box, "direction": direction, "symbol": "X" if direction == "X" else "O"}
        )

plot_df = pd.DataFrame(plot_data)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Plot X's (bullish) and O's (bearish) using seaborn scatterplot with markers
x_data = plot_df[plot_df["direction"] == "X"]
o_data = plot_df[plot_df["direction"] == "O"]

# Use seaborn scatterplot for each direction with custom markers
if not x_data.empty:
    sns.scatterplot(
        data=x_data, x="column", y="price", marker="x", s=400, linewidth=3, color="#2E7D32", ax=ax, legend=False
    )

if not o_data.empty:
    sns.scatterplot(
        data=o_data,
        x="column",
        y="price",
        marker="o",
        s=300,
        facecolors="none",
        edgecolor="#C62828",
        linewidth=3,
        ax=ax,
        legend=False,
    )

# Add legend manually
ax.scatter([], [], marker="x", s=400, linewidth=3, color="#2E7D32", label="X (Rising)")
ax.scatter([], [], marker="o", s=300, facecolors="none", edgecolor="#C62828", linewidth=3, label="O (Falling)")
ax.legend(loc="upper left", fontsize=16, frameon=True, framealpha=0.9)

# Styling
ax.set_xlabel("Column (Reversals)", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.set_title("point-and-figure-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set y-axis to show box boundaries
price_min = plot_df["price"].min() - box_size
price_max = plot_df["price"].max() + box_size
yticks = np.arange(int(price_min / box_size) * box_size, price_max + box_size, box_size * 2)
ax.set_yticks(yticks)
ax.set_ylim(price_min, price_max)

# Subtle grid aligned to boxes
ax.yaxis.grid(True, alpha=0.3, linestyle="--")
ax.xaxis.grid(True, alpha=0.2, linestyle=":")

# Set x-axis limits with some padding
ax.set_xlim(-0.5, plot_df["column"].max() + 0.5)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
