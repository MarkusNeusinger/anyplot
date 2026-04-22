""" pyplots.ai
point-and-figure-basic: Point and Figure Chart
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Generate synthetic stock price data
np.random.seed(42)
n_days = 300

# Start price and generate realistic daily returns
start_price = 100
daily_returns = np.random.normal(0.0005, 0.015, n_days)

# Add some trending periods
daily_returns[50:80] += 0.003  # Uptrend
daily_returns[100:140] -= 0.004  # Downtrend
daily_returns[180:220] += 0.0035  # Uptrend
daily_returns[240:280] -= 0.003  # Downtrend

close_prices = start_price * np.cumprod(1 + daily_returns)

# Generate high/low based on close
volatility = np.abs(np.random.normal(0, 0.01, n_days))
high_prices = close_prices * (1 + volatility)
low_prices = close_prices * (1 - volatility)

dates = pd.date_range("2024-01-01", periods=n_days, freq="D")

df = pd.DataFrame({"date": dates, "high": high_prices, "low": low_prices, "close": close_prices})

# Point and Figure calculation
box_size = 2.0  # Each box represents $2
reversal = 3  # 3-box reversal

# Calculate P&F columns
columns = []
current_direction = None  # 'X' for up, 'O' for down
current_column_start = None
current_column_end = None

# Initialize with first price
first_price = df["close"].iloc[0]
box_start = np.floor(first_price / box_size) * box_size

for _i, row in df.iterrows():
    price = row["close"]
    box_price = np.floor(price / box_size) * box_size

    if current_direction is None:
        # Initialize first direction based on next movement
        current_column_start = box_start
        current_column_end = box_start
        # Wait for significant move
        if price >= box_start + box_size:
            current_direction = "X"
            current_column_end = box_price
        elif price <= box_start - box_size:
            current_direction = "O"
            current_column_end = box_price
    else:
        if current_direction == "X":
            # In uptrend
            if box_price >= current_column_end + box_size:
                # Continue up
                current_column_end = box_price
            elif box_price <= current_column_end - reversal * box_size:
                # Reversal down - save current column and start new O column
                columns.append({"type": "X", "start": current_column_start, "end": current_column_end})
                current_direction = "O"
                current_column_start = current_column_end - box_size
                current_column_end = box_price
        else:
            # In downtrend
            if box_price <= current_column_end - box_size:
                # Continue down
                current_column_end = box_price
            elif box_price >= current_column_end + reversal * box_size:
                # Reversal up - save current column and start new X column
                columns.append({"type": "O", "start": current_column_start, "end": current_column_end})
                current_direction = "X"
                current_column_start = current_column_end + box_size
                current_column_end = box_price

# Save the last column
if current_direction is not None:
    columns.append({"type": current_direction, "start": current_column_start, "end": current_column_end})

# Prepare data for plotting
x_data = []
o_data = []

for col_idx, col in enumerate(columns):
    if col["type"] == "X":
        start = min(col["start"], col["end"])
        end = max(col["start"], col["end"])
        boxes = np.arange(start, end + box_size / 2, box_size)
        for box in boxes:
            x_data.append({"col": col_idx, "price": box})
    else:
        start = max(col["start"], col["end"])
        end = min(col["start"], col["end"])
        boxes = np.arange(end, start + box_size / 2, box_size)
        for box in boxes:
            o_data.append({"col": col_idx, "price": box})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="point-and-figure-basic · bokeh · pyplots.ai",
    x_axis_label="Column (Reversal)",
    y_axis_label="Price ($)",
)

# Style settings - scaled for 4800x2700 canvas
p.title.text_font_size = "48pt"
p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.major_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "28pt"

# Background and grid
p.background_fill_color = "#fafafa"
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"
p.xgrid.grid_line_color = "#cccccc"
p.ygrid.grid_line_color = "#cccccc"

# Plot X markers (bullish - green)
if x_data:
    x_source = ColumnDataSource(data={"col": [d["col"] for d in x_data], "price": [d["price"] for d in x_data]})
    p.text(
        x="col",
        y="price",
        text={"value": "X"},
        source=x_source,
        text_font_size="48pt",
        text_color="#2E7D32",
        text_align="center",
        text_baseline="middle",
        text_font_style="bold",
    )

# Plot O markers (bearish - red)
if o_data:
    o_source = ColumnDataSource(data={"col": [d["col"] for d in o_data], "price": [d["price"] for d in o_data]})
    p.text(
        x="col",
        y="price",
        text={"value": "O"},
        source=o_source,
        text_font_size="48pt",
        text_color="#C62828",
        text_align="center",
        text_baseline="middle",
        text_font_style="bold",
    )

# Add support trend line (45-degree ascending from low)
all_prices = [d["price"] for d in x_data] + [d["price"] for d in o_data]
if all_prices:
    min_price = min(all_prices)
    max_price = max(all_prices)

    # Find lowest point for support line
    support_start_col = 0
    support_start_price = min_price - box_size
    support_end_col = len(columns) - 1
    support_end_price = support_start_price + (support_end_col - support_start_col) * box_size

    if support_end_price <= max_price + 2 * box_size:
        p.line(
            x=[support_start_col, support_end_col],
            y=[support_start_price, support_end_price],
            line_width=5,
            line_color="#306998",
            line_dash="solid",
            legend_label="Support Trend",
        )

    # Find highest point for resistance line
    resistance_start_col = 0
    resistance_start_price = max_price + box_size
    resistance_end_col = len(columns) - 1
    resistance_end_price = resistance_start_price - (resistance_end_col - resistance_start_col) * box_size

    if resistance_end_price >= min_price - 2 * box_size:
        p.line(
            x=[resistance_start_col, resistance_end_col],
            y=[resistance_start_price, resistance_end_price],
            line_width=5,
            line_color="#FFD43B",
            line_dash="solid",
            legend_label="Resistance Trend",
        )

# Legend styling
p.legend.location = "top_left"
p.legend.label_text_font_size = "28pt"
p.legend.background_fill_alpha = 0.8
p.legend.glyph_height = 30
p.legend.glyph_width = 30

# Save as PNG and HTML (interactive)
export_png(p, filename="plot.png")
save(p, filename="plot.html")
