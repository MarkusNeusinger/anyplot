""" pyplots.ai
line-timeseries: Time Series Line Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Daily stock prices over one year
np.random.seed(42)

# Generate 252 trading days (one year of stock market data)
dates = pd.date_range(start="2024-01-02", periods=252, freq="B")

# Simulate stock price with trend and volatility
price = 100.0
prices = [price]
for _ in range(251):
    # Random walk with slight upward drift
    change = np.random.randn() * 2 + 0.05
    price = max(price + change, 50)  # Floor at 50
    prices.append(price)

df = pd.DataFrame({"date": dates, "price": prices})

# Create time series line chart
chart = (
    alt.Chart(df)
    .mark_line(
        strokeWidth=3,
        color="#306998",  # Python Blue
    )
    .encode(
        x=alt.X(
            "date:T",
            title="Date",
            axis=alt.Axis(
                format="%b %Y",  # Month Year format
                labelFontSize=18,
                titleFontSize=22,
                labelAngle=-45,
                tickCount=12,
            ),
        ),
        y=alt.Y(
            "price:Q",
            title="Stock Price ($)",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.3),
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%B %d, %Y"),
            alt.Tooltip("price:Q", title="Price", format="$.2f"),
        ],
    )
    .properties(
        width=1600, height=900, title=alt.Title("line-timeseries · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_view(strokeWidth=0)
    .configure_axis(gridColor="#cccccc", gridOpacity=0.3, domainColor="#333333")
    .interactive()
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
