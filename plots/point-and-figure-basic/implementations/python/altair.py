""" pyplots.ai
point-and-figure-basic: Point and Figure Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import altair as alt
import numpy as np
import pandas as pd


# Generate synthetic stock price data
np.random.seed(42)
n_days = 300
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")

# Random walk for close prices starting at $100
returns = np.random.normal(0.0005, 0.02, n_days)
close = 100 * np.cumprod(1 + returns)

# Generate high/low around close
high = close * (1 + np.random.uniform(0.005, 0.02, n_days))
low = close * (1 - np.random.uniform(0.005, 0.02, n_days))

df = pd.DataFrame({"date": dates, "high": high, "low": low, "close": close})

# Point and Figure parameters
box_size = 2.0  # $2 per box
reversal = 3  # 3-box reversal

# Build Point and Figure columns
pf_data = []
column = 0
direction = None  # 'X' for up, 'O' for down
current_price = close[0]
column_start = round(current_price / box_size) * box_size

for i in range(1, len(close)):
    price = close[i]

    if direction is None:
        # Initialize direction based on first significant move
        if price >= column_start + box_size:
            direction = "X"
            boxes_up = int((price - column_start) / box_size)
            for b in range(boxes_up + 1):
                pf_data.append(
                    {"column": column, "price": column_start + b * box_size, "symbol": "X", "color": "bullish"}
                )
            current_price = column_start + boxes_up * box_size
        elif price <= column_start - box_size:
            direction = "O"
            boxes_down = int((column_start - price) / box_size)
            for b in range(boxes_down + 1):
                pf_data.append(
                    {"column": column, "price": column_start - b * box_size, "symbol": "O", "color": "bearish"}
                )
            current_price = column_start - boxes_down * box_size
    elif direction == "X":
        # In X column (rising)
        if price >= current_price + box_size:
            # Continue up
            boxes_up = int((price - current_price) / box_size)
            for b in range(1, boxes_up + 1):
                pf_data.append(
                    {"column": column, "price": current_price + b * box_size, "symbol": "X", "color": "bullish"}
                )
            current_price = current_price + boxes_up * box_size
        elif price <= current_price - reversal * box_size:
            # Reversal to O column
            column += 1
            boxes_down = int((current_price - price) / box_size)
            new_start = current_price - box_size  # Start one box below last X
            for b in range(boxes_down):
                pf_data.append({"column": column, "price": new_start - b * box_size, "symbol": "O", "color": "bearish"})
            current_price = new_start - (boxes_down - 1) * box_size
            direction = "O"
    else:
        # In O column (falling)
        if price <= current_price - box_size:
            # Continue down
            boxes_down = int((current_price - price) / box_size)
            for b in range(1, boxes_down + 1):
                pf_data.append(
                    {"column": column, "price": current_price - b * box_size, "symbol": "O", "color": "bearish"}
                )
            current_price = current_price - boxes_down * box_size
        elif price >= current_price + reversal * box_size:
            # Reversal to X column
            column += 1
            boxes_up = int((price - current_price) / box_size)
            new_start = current_price + box_size  # Start one box above last O
            for b in range(boxes_up):
                pf_data.append({"column": column, "price": new_start + b * box_size, "symbol": "X", "color": "bullish"})
            current_price = new_start + (boxes_up - 1) * box_size
            direction = "X"

pf_df = pd.DataFrame(pf_data)

# Create Point and Figure chart
chart = (
    alt.Chart(pf_df)
    .mark_text(fontSize=24, fontWeight="bold")
    .encode(
        x=alt.X("column:O", title="Column (Reversals)", axis=alt.Axis(labelFontSize=16, titleFontSize=20)),
        y=alt.Y(
            "price:Q",
            title="Price ($)",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(labelFontSize=16, titleFontSize=20, format="$.0f"),
        ),
        text="symbol:N",
        color=alt.Color(
            "color:N",
            scale=alt.Scale(domain=["bullish", "bearish"], range=["#306998", "#d62728"]),
            legend=alt.Legend(title="Direction", labelFontSize=14, titleFontSize=16),
        ),
        tooltip=[
            alt.Tooltip("column:O", title="Column"),
            alt.Tooltip("price:Q", title="Price", format="$.2f"),
            alt.Tooltip("symbol:N", title="Symbol"),
        ],
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "point-and-figure-basic · altair · pyplots.ai",
            fontSize=28,
            subtitle=f"Box Size: ${box_size:.0f} | Reversal: {reversal} boxes",
            subtitleFontSize=18,
        ),
    )
    .configure_axis(grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
