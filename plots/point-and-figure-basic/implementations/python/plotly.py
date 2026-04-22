""" pyplots.ai
point-and-figure-basic: Point and Figure Chart
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import numpy as np
import plotly.graph_objects as go


# Generate synthetic stock price data
np.random.seed(42)
n_days = 300

# Create realistic price movement with trends
initial_price = 100.0
returns = np.random.normal(0.001, 0.02, n_days)

# Add some trend phases
returns[50:100] += 0.003  # Uptrend
returns[120:150] -= 0.004  # Downtrend
returns[180:230] += 0.002  # Mild uptrend
returns[250:280] -= 0.003  # Downtrend

close = initial_price * np.cumprod(1 + returns)
high = close * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
low = close * (1 - np.abs(np.random.normal(0, 0.01, n_days)))

# Point and Figure calculation parameters
box_size = 2.0  # $2 per box
reversal = 3  # 3-box reversal

# Build P&F chart columns
columns = []  # List of (start_price, end_price, direction, column_index)
current_direction = None  # 'X' for up, 'O' for down
current_column = []
column_index = 0

# Initialize with first close price
current_price = np.floor(close[0] / box_size) * box_size

for i in range(1, len(close)):
    price = close[i]

    if current_direction is None:
        # Determine initial direction
        price_boxes = np.floor(price / box_size) * box_size
        if price_boxes > current_price + box_size:
            current_direction = "X"
            for p in np.arange(current_price, price_boxes + box_size, box_size):
                current_column.append(p)
            current_price = price_boxes
        elif price_boxes < current_price - box_size:
            current_direction = "O"
            for p in np.arange(current_price, price_boxes - box_size, -box_size):
                current_column.append(p)
            current_price = price_boxes
    else:
        price_boxes = np.floor(price / box_size) * box_size

        if current_direction == "X":
            # Continue up or reverse down
            if price_boxes > current_price:
                for p in np.arange(current_price + box_size, price_boxes + box_size, box_size):
                    current_column.append(p)
                current_price = price_boxes
            elif price_boxes <= current_price - reversal * box_size:
                # Reversal - save current column and start new O column
                if current_column:
                    columns.append((current_column.copy(), "X", column_index))
                    column_index += 1
                current_direction = "O"
                current_column = []
                for p in np.arange(current_price - box_size, price_boxes - box_size, -box_size):
                    current_column.append(p)
                current_price = price_boxes
        else:
            # Continue down or reverse up
            if price_boxes < current_price:
                for p in np.arange(current_price - box_size, price_boxes - box_size, -box_size):
                    current_column.append(p)
                current_price = price_boxes
            elif price_boxes >= current_price + reversal * box_size:
                # Reversal - save current column and start new X column
                if current_column:
                    columns.append((current_column.copy(), "O", column_index))
                    column_index += 1
                current_direction = "X"
                current_column = []
                for p in np.arange(current_price + box_size, price_boxes + box_size, box_size):
                    current_column.append(p)
                current_price = price_boxes

# Add final column
if current_column:
    columns.append((current_column.copy(), current_direction, column_index))

# Create figure
fig = go.Figure()

# Plot each column
for prices, direction, col_idx in columns:
    if not prices:
        continue

    x_positions = [col_idx] * len(prices)
    symbol = "X" if direction == "X" else "O"
    color = "#2E7D32" if direction == "X" else "#C62828"  # Green for X, Red for O

    fig.add_trace(
        go.Scatter(
            x=x_positions,
            y=prices,
            mode="text",
            text=[symbol] * len(prices),
            textfont=dict(size=18, color=color, family="Arial Black"),
            showlegend=False,
            hovertemplate=f"Column: {col_idx}<br>Price: %{{y:.0f}}<br>{direction}<extra></extra>",
        )
    )

# Add legend entries (dummy traces)
fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="text",
        text=["X"],
        textfont=dict(size=18, color="#2E7D32", family="Arial Black"),
        name="X (Rising)",
        showlegend=True,
    )
)

fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="text",
        text=["O"],
        textfont=dict(size=18, color="#C62828", family="Arial Black"),
        name="O (Falling)",
        showlegend=True,
    )
)

# Calculate price range for axis
all_prices = []
for prices, _, _ in columns:
    all_prices.extend(prices)

if all_prices:
    min_price = min(all_prices) - box_size * 2
    max_price = max(all_prices) + box_size * 2
else:
    min_price, max_price = 80, 130

# Update layout
fig.update_layout(
    title=dict(
        text="point-and-figure-basic · plotly · pyplots.ai",
        font=dict(size=28, color="#333333"),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text="Column (Reversal)", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.1)",
        zeroline=False,
        dtick=5,
    ),
    yaxis=dict(
        title=dict(text="Price ($)", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.1)",
        dtick=box_size * 2,
        range=[min_price, max_price],
    ),
    template="plotly_white",
    legend=dict(
        font=dict(size=18),
        x=1.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="rgba(0,0,0,0.2)",
        borderwidth=1,
    ),
    margin=dict(l=80, r=150, t=100, b=80),
    plot_bgcolor="white",
)

# Add annotation for parameters
fig.add_annotation(
    text=f"Box Size: ${box_size:.0f} | Reversal: {reversal} boxes",
    xref="paper",
    yref="paper",
    x=0.5,
    y=-0.12,
    showarrow=False,
    font=dict(size=16, color="#666666"),
    xanchor="center",
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
