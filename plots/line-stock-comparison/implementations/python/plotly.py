""" pyplots.ai
line-stock-comparison: Stock Price Comparison Chart
Library: plotly 6.5.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Generate synthetic stock price data for 4 companies
np.random.seed(42)
n_days = 252  # Approximately 1 year of trading days
date_range = pd.date_range(start="2024-01-01", periods=n_days, freq="B")

# Define stocks with different volatility and drift characteristics
stocks = {
    "AAPL": {"drift": 0.0008, "volatility": 0.018},
    "GOOGL": {"drift": 0.0006, "volatility": 0.020},
    "MSFT": {"drift": 0.0007, "volatility": 0.016},
    "SPY": {"drift": 0.0004, "volatility": 0.012},
}

# Generate price paths using geometric Brownian motion
price_data = {}
for symbol, params in stocks.items():
    returns = np.random.normal(params["drift"], params["volatility"], n_days)
    # Start with a realistic base price (not used directly, but helps with generation)
    prices = 100 * np.exp(np.cumsum(returns))
    price_data[symbol] = prices

# Create DataFrame
df = pd.DataFrame(price_data, index=date_range)

# Normalize all series to 100 at the starting point (rebasing)
df_rebased = (df / df.iloc[0]) * 100

# Plot - Create comparison chart
fig = go.Figure()

# Color palette for stocks
colors = ["#306998", "#FFD43B", "#E74C3C", "#2ECC71"]

for i, symbol in enumerate(stocks.keys()):
    fig.add_trace(
        go.Scatter(
            x=df_rebased.index,
            y=df_rebased[symbol],
            mode="lines",
            name=symbol,
            line={"width": 3, "color": colors[i]},
            hovertemplate=f"{symbol}<br>Date: %{{x|%Y-%m-%d}}<br>Value: %{{y:.1f}}<extra></extra>",
        )
    )

# Add horizontal reference line at 100
fig.add_hline(
    y=100,
    line_dash="dash",
    line_color="gray",
    line_width=2,
    annotation_text="Starting Point (100)",
    annotation_position="bottom right",
    annotation_font_size=14,
)

# Layout
fig.update_layout(
    title={"text": "line-stock-comparison · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Date", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(128, 128, 128, 0.2)",
    },
    yaxis={
        "title": {"text": "Rebased Price (Starting = 100)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(128, 128, 128, 0.2)",
    },
    template="plotly_white",
    legend={"font": {"size": 18}, "orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "center", "x": 0.5},
    margin={"l": 80, "r": 40, "t": 120, "b": 80},
    hovermode="x unified",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
