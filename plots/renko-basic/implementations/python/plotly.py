""" pyplots.ai
renko-basic: Basic Renko Chart
Library: plotly 6.5.1 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Generate synthetic stock price data
np.random.seed(42)
n_days = 250
dates = pd.date_range("2025-01-01", periods=n_days, freq="D")
returns = np.random.randn(n_days) * 0.02  # 2% daily volatility
prices = 100 * np.exp(np.cumsum(returns))  # Geometric random walk starting at $100

# Renko brick calculation
brick_size = 2.0  # $2 brick size


def calculate_renko(prices, brick_size):
    """Calculate Renko bricks from price data."""
    bricks = []
    if len(prices) == 0:
        return bricks

    current_price = prices[0]
    # Round to nearest brick size
    base_price = round(current_price / brick_size) * brick_size

    for price in prices[1:]:
        diff = price - base_price
        num_bricks = int(abs(diff) // brick_size)

        if num_bricks >= 1:
            direction = 1 if diff > 0 else -1
            for _ in range(num_bricks):
                brick_open = base_price
                brick_close = base_price + direction * brick_size
                bricks.append(
                    {"open": brick_open, "close": brick_close, "direction": "up" if direction > 0 else "down"}
                )
                base_price = brick_close

    return bricks


bricks = calculate_renko(prices, brick_size)

# Prepare data for plotting
brick_indices = list(range(len(bricks)))
opens = [b["open"] for b in bricks]
closes = [b["close"] for b in bricks]
directions = [b["direction"] for b in bricks]

# Separate up and down bricks for coloring
up_mask = [d == "up" for d in directions]
down_mask = [d == "down" for d in directions]

# Create figure
fig = go.Figure()

# Add up bricks (bullish - green)
for i, brick in enumerate(bricks):
    if brick["direction"] == "up":
        fig.add_trace(
            go.Bar(
                x=[i],
                y=[brick_size],
                base=brick["open"],
                marker=dict(color="#2ECC71", line=dict(color="#27AE60", width=1.5)),
                width=0.85,
                showlegend=False,
                hovertemplate=f"Brick {i + 1}<br>Open: ${brick['open']:.2f}<br>Close: ${brick['close']:.2f}<br>Type: Bullish<extra></extra>",
            )
        )

# Add down bricks (bearish - red)
for i, brick in enumerate(bricks):
    if brick["direction"] == "down":
        fig.add_trace(
            go.Bar(
                x=[i],
                y=[brick_size],
                base=brick["close"],
                marker=dict(color="#E74C3C", line=dict(color="#C0392B", width=1.5)),
                width=0.85,
                showlegend=False,
                hovertemplate=f"Brick {i + 1}<br>Open: ${brick['open']:.2f}<br>Close: ${brick['close']:.2f}<br>Type: Bearish<extra></extra>",
            )
        )

# Add legend traces
fig.add_trace(
    go.Bar(
        x=[None],
        y=[None],
        marker=dict(color="#2ECC71", line=dict(color="#27AE60", width=1.5)),
        name="Bullish (Up)",
        showlegend=True,
    )
)
fig.add_trace(
    go.Bar(
        x=[None],
        y=[None],
        marker=dict(color="#E74C3C", line=dict(color="#C0392B", width=1.5)),
        name="Bearish (Down)",
        showlegend=True,
    )
)

# Update layout
fig.update_layout(
    title=dict(text="renko-basic · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Brick Index", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(128, 128, 128, 0.2)",
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Price (USD)", font=dict(size=24)),
        tickfont=dict(size=18),
        tickformat="$.0f",
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(128, 128, 128, 0.2)",
        zeroline=False,
    ),
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    legend=dict(font=dict(size=18), orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    bargap=0.15,
    margin=dict(l=100, r=50, t=120, b=80),
)

# Add annotation for brick size
fig.add_annotation(
    text=f"Brick Size: ${brick_size:.2f}",
    xref="paper",
    yref="paper",
    x=0.99,
    y=0.01,
    xanchor="right",
    yanchor="bottom",
    font=dict(size=16, color="gray"),
    showarrow=False,
)

# Save as PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
