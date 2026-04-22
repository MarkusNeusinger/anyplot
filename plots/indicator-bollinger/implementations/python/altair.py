""" pyplots.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulated stock price with realistic Bollinger Bands
np.random.seed(42)
n_days = 120
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")  # Business days

# Generate price series with trend and volatility changes
returns = np.random.randn(n_days) * 0.015  # Daily returns ~1.5% std
# Add some trending behavior
returns[:30] += 0.002  # Uptrend start
returns[50:70] -= 0.003  # Downtrend middle
returns[90:] += 0.002  # Recovery end
price = 100 * np.cumprod(1 + returns)

# Calculate Bollinger Bands (20-period SMA, 2 std deviations)
window = 20
sma = pd.Series(price).rolling(window=window).mean()
std = pd.Series(price).rolling(window=window).std()
upper_band = sma + 2 * std
lower_band = sma - 2 * std

# Create DataFrame starting from period 20 (where we have valid SMA)
df = pd.DataFrame(
    {
        "date": dates[window - 1 :],
        "close": price[window - 1 :],
        "sma": sma[window - 1 :].values,
        "upper_band": upper_band[window - 1 :].values,
        "lower_band": lower_band[window - 1 :].values,
    }
)

# Calculate Y-axis range with some padding
y_min = df[["close", "lower_band"]].min().min() * 0.98
y_max = df[["close", "upper_band"]].max().max() * 1.02

# Base chart configuration
base = alt.Chart(df).encode(
    x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %d", labelAngle=-45, tickCount=10))
)

# Band area (filled region between upper and lower bands)
band_area = (
    alt.Chart(df)
    .mark_area(opacity=0.25, color="#306998")
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("lower_band:Q", title="Price ($)", scale=alt.Scale(domain=[y_min, y_max])),
        y2="upper_band:Q",
    )
)

# Upper band line
upper_line = base.mark_line(strokeWidth=2, color="#306998", opacity=0.7).encode(
    y=alt.Y("upper_band:Q", scale=alt.Scale(domain=[y_min, y_max]))
)

# Lower band line
lower_line = base.mark_line(strokeWidth=2, color="#306998", opacity=0.7).encode(
    y=alt.Y("lower_band:Q", scale=alt.Scale(domain=[y_min, y_max]))
)

# Middle band (SMA) - dashed line
sma_line = base.mark_line(strokeWidth=2.5, strokeDash=[8, 4], color="#306998").encode(
    y=alt.Y("sma:Q", scale=alt.Scale(domain=[y_min, y_max]))
)

# Price line - prominent
price_line = base.mark_line(strokeWidth=3, color="#FFD43B").encode(
    y=alt.Y("close:Q", scale=alt.Scale(domain=[y_min, y_max]))
)

# Combine all layers
chart = (
    alt.layer(band_area, upper_line, lower_line, sma_line, price_line)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("indicator-bollinger · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
