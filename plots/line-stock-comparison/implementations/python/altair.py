""" pyplots.ai
line-stock-comparison: Stock Price Comparison Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Generate synthetic stock price data for 4 stocks over ~1 year
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=252, freq="B")  # Business days

# Simulate stock prices with different trends and volatility
symbols = ["AAPL", "GOOGL", "MSFT", "SPY"]
returns_params = {
    "AAPL": (0.0008, 0.018),  # Higher return, moderate volatility
    "GOOGL": (0.0004, 0.022),  # Moderate return, higher volatility
    "MSFT": (0.0006, 0.016),  # Moderate return, lower volatility
    "SPY": (0.0004, 0.012),  # Index: lower return, lower volatility
}

data_list = []
for symbol in symbols:
    mean_return, volatility = returns_params[symbol]
    returns = np.random.normal(mean_return, volatility, len(dates))
    prices = 100 * np.cumprod(1 + returns)  # Start at 100 (already rebased)

    for date, price in zip(dates, prices, strict=True):
        data_list.append({"date": date, "symbol": symbol, "rebased_price": price})

df = pd.DataFrame(data_list)

# Create chart with multi-line encoding
base = alt.Chart(df).encode(
    x=alt.X("date:T", title="Date", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
    y=alt.Y("rebased_price:Q", title="Rebased Price (Start = 100)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
    color=alt.Color(
        "symbol:N",
        title="Symbol",
        scale=alt.Scale(domain=["AAPL", "GOOGL", "MSFT", "SPY"], range=["#306998", "#FFD43B", "#E34A33", "#31A354"]),
        legend=alt.Legend(titleFontSize=20, labelFontSize=18, symbolSize=300),
    ),
)

# Line chart
lines = base.mark_line(strokeWidth=3)

# Reference line at 100
reference_line = (
    alt.Chart(pd.DataFrame({"y": [100]})).mark_rule(color="gray", strokeDash=[6, 4], strokeWidth=2).encode(y="y:Q")
)

# Combine layers
chart = (
    alt.layer(reference_line, lines)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("line-stock-comparison · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(grid=True, gridColor="#E0E0E0", gridOpacity=0.5)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
