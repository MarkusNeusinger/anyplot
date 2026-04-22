""" pyplots.ai
point-and-figure-basic: Point and Figure Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 72/100 | Created: 2026-01-15
"""

import numpy as np
import pygal
from pygal.style import Style


# Random seed for reproducibility
np.random.seed(42)

# Generate realistic stock price data (6 months of daily data)
n_days = 150
base_price = 100.0
returns = np.random.normal(0.001, 0.02, n_days)
prices = base_price * np.cumprod(1 + returns)

# P&F parameters
box_size = 2.0
reversal = 3

# Calculate P&F chart data - inline rounding (KISS - no helper functions)
columns = []
current_direction = None
current_column_start = np.floor(prices[0] / box_size) * box_size
current_column_end = current_column_start

for price in prices[1:]:
    rounded_price = np.floor(price / box_size) * box_size

    if current_direction is None:
        if rounded_price >= current_column_end + box_size:
            current_direction = "X"
            current_column_end = rounded_price
        elif rounded_price <= current_column_end - box_size:
            current_direction = "O"
            current_column_end = rounded_price
    elif current_direction == "X":
        if rounded_price >= current_column_end + box_size:
            current_column_end = rounded_price
        elif rounded_price <= current_column_end - (reversal * box_size):
            columns.append((current_column_start, current_column_end, "X"))
            current_column_start = current_column_end - box_size
            current_column_end = rounded_price
            current_direction = "O"
    else:
        if rounded_price <= current_column_end - box_size:
            current_column_end = rounded_price
        elif rounded_price >= current_column_end + (reversal * box_size):
            columns.append((current_column_start, current_column_end, "O"))
            current_column_start = current_column_end + box_size
            current_column_end = rounded_price
            current_direction = "X"

if current_direction:
    columns.append((current_column_start, current_column_end, current_direction))

# Colorblind-safe colors (blue for rising X, orange for falling O)
x_color = "#0066CC"
o_color = "#E56B00"
support_color = "#228B22"
resistance_color = "#8B0000"

# Custom style with subtle grid
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#DDDDDD",  # Subtle grid lines
    colors=(x_color, o_color, support_color, resistance_color),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=48,
    value_font_size=42,
    tooltip_font_size=36,
    stroke_width=6,
    guide_stroke_dasharray="4,4",  # Dashed grid for subtlety
)

# Collect price range
all_prices = []
for start, end, _ in columns:
    all_prices.extend([start, end])

y_min = min(all_prices) - box_size
y_max = max(all_prices) + box_size
y_labels = list(np.arange(y_min, y_max + box_size, box_size))

# Create XY chart with visible dots for X and O markers
# Pygal uses circles as markers - distinguish X/O through color and legend
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="point-and-figure-basic · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    show_y_guides=True,
    show_x_guides=False,  # Only horizontal guides for cleaner look
    x_title="Column (Reversal)",
    y_title="Price ($)",
    margin=50,
    margin_bottom=200,
    margin_left=200,
    margin_top=150,
    margin_right=120,  # Better balance
    y_labels=y_labels,
    range=(y_min, y_max),
    dots_size=22,
    stroke=False,
)

# Build X and O data points
x_points = []
o_points = []

for col_idx, (start, end, direction) in enumerate(columns):
    low = min(start, end)
    high = max(start, end)
    if direction == "X":
        for price_level in np.arange(low, high + box_size, box_size):
            x_points.append((col_idx, price_level))
    else:
        for price_level in np.arange(low, high + box_size, box_size):
            o_points.append((col_idx, price_level))

# Add series - X markers (rising) and O markers (falling)
# Legend clearly shows X and O symbols to identify the markers
chart.add("X (Rising)", x_points, stroke=False)
chart.add("O (Falling)", o_points, stroke=False)

# Calculate support and resistance trend lines
support_lows = []
resistance_highs = []

for col_idx, (start, end, direction) in enumerate(columns):
    low = min(start, end)
    high = max(start, end)
    if direction == "O":
        support_lows.append((col_idx, low))
    else:
        resistance_highs.append((col_idx, high))

# Support line (45-degree uptrend from O column lows) - with visible endpoints
if len(support_lows) >= 2:
    support_start = support_lows[0]
    support_end_col = min(support_start[0] + 5, len(columns) - 1)
    support_line = [
        (support_start[0], support_start[1]),
        (support_end_col, support_start[1] + (support_end_col - support_start[0]) * box_size),
    ]
    chart.add("Support (45° up)", support_line, stroke=True, dots_size=10)

# Resistance line (45-degree downtrend from X column highs) - with visible endpoints
if len(resistance_highs) >= 2:
    resistance_start = resistance_highs[0]
    resistance_end_col = min(resistance_start[0] + 5, len(columns) - 1)
    resistance_line = [
        (resistance_start[0], resistance_start[1]),
        (resistance_end_col, resistance_start[1] - (resistance_end_col - resistance_start[0]) * box_size),
    ]
    chart.add("Resistance (45° down)", resistance_line, stroke=True, dots_size=10)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
