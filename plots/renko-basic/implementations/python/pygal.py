""" pyplots.ai
renko-basic: Basic Renko Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import numpy as np
import pygal
from pygal.style import Style


# Seed for reproducibility
np.random.seed(42)

# Generate synthetic stock price data (6 months of daily closes)
n_days = 180
initial_price = 100
returns = np.random.normal(0.001, 0.02, n_days)  # Daily returns with drift
prices = initial_price * np.cumprod(1 + returns)

# Renko brick calculation
brick_size = 2.0  # $2 per brick

# Build Renko bricks from price data
bricks = []
current_brick_price = round(prices[0] / brick_size) * brick_size
direction = None  # None, 'up', or 'down'

for price in prices:
    while True:
        if direction is None:
            # First brick - determine initial direction
            if price >= current_brick_price + brick_size:
                bricks.append({"price": current_brick_price, "direction": "up"})
                current_brick_price += brick_size
                direction = "up"
            elif price <= current_brick_price - brick_size:
                bricks.append({"price": current_brick_price - brick_size, "direction": "down"})
                current_brick_price -= brick_size
                direction = "down"
            else:
                break
        elif direction == "up":
            if price >= current_brick_price + brick_size:
                bricks.append({"price": current_brick_price, "direction": "up"})
                current_brick_price += brick_size
            elif price <= current_brick_price - 2 * brick_size:
                # Reversal requires 2 bricks in opposite direction
                current_brick_price -= brick_size
                bricks.append({"price": current_brick_price - brick_size, "direction": "down"})
                current_brick_price -= brick_size
                direction = "down"
            else:
                break
        else:  # direction == 'down'
            if price <= current_brick_price - brick_size:
                bricks.append({"price": current_brick_price - brick_size, "direction": "down"})
                current_brick_price -= brick_size
            elif price >= current_brick_price + 2 * brick_size:
                # Reversal requires 2 bricks in opposite direction
                current_brick_price += brick_size
                bricks.append({"price": current_brick_price, "direction": "up"})
                current_brick_price += brick_size
                direction = "up"
            else:
                break

# Limit to reasonable number of bricks for display
bricks = bricks[:40] if len(bricks) > 40 else bricks

# Calculate price range for chart
min_price = min(b["price"] for b in bricks)
max_price = max(b["price"] for b in bricks) + brick_size

# Custom style for high resolution (4800x2700)
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=("#fafafa", "#22c55e", "#ef4444"),  # Spacer (invisible), Green, Red
    title_font_size=52,
    label_font_size=32,
    major_label_font_size=28,
    legend_font_size=32,
    value_font_size=24,
    tooltip_font_size=24,
    guide_stroke_color="#e0e0e0",
    major_guide_stroke_color="#ccc",
)

# Calculate y-axis range
y_min = min_price - brick_size
y_max = max_price + brick_size

# Create StackedBar chart for Renko representation
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    title="renko-basic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Brick Index",
    y_title="Price ($)",
    style=custom_style,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    show_y_guides=True,
    show_x_guides=False,
    print_values=False,
    spacing=6,
    margin=100,
    margin_bottom=180,
    margin_left=120,
    truncate_legend=-1,
)

# Set x-axis labels (show every 5th index)
chart.x_labels = [str(i) if i % 5 == 0 else "" for i in range(len(bricks))]

# Create y-axis labels with actual price values
# The stacked bar y-axis is relative, so we label what the values represent
y_labels = []
for y in range(int(y_min), int(y_max) + 1, int(brick_size * 2)):
    y_labels.append(f"${y}")
chart.y_labels = y_labels

# Build data for each series
spacer_values = []  # Height from 0 to brick bottom (invisible)
up_values = []  # Height of bullish brick
down_values = []  # Height of bearish brick

for brick in bricks:
    # Spacer = height from y_min to brick bottom
    spacer_height = brick["price"] - y_min
    spacer_values.append(spacer_height)

    if brick["direction"] == "up":
        up_values.append(brick_size)
        down_values.append(None)
    else:
        up_values.append(None)
        down_values.append(brick_size)

# Add series in stack order (bottom to top)
chart.add("", spacer_values)  # Empty name hides from legend
chart.add("Bullish (Up)", up_values)
chart.add("Bearish (Down)", down_values)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
