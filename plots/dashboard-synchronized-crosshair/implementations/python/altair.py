""" pyplots.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Stock-like data with price, volume, and technical indicator
np.random.seed(42)
n_points = 200
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

# Price (random walk)
returns = np.random.normal(0.001, 0.02, n_points)
price = 100 * np.cumprod(1 + returns)

# Volume (correlated with absolute returns)
base_volume = np.random.uniform(1e6, 3e6, n_points)
volume = base_volume * (1 + np.abs(returns) * 20)

# Technical indicator (momentum-like, range 0-100)
indicator = 50 + np.cumsum(np.random.normal(0, 5, n_points))
indicator = np.clip(indicator, 0, 100)

df = pd.DataFrame({"date": dates, "price": price, "volume": volume, "indicator": indicator})

# Create synchronized selection for crosshair
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["date"], empty=False)

# Base chart with shared x-axis
base = alt.Chart(df).encode(x=alt.X("date:T", axis=alt.Axis(format="%b %Y", labelFontSize=14, titleFontSize=18)))

# Vertical rule (crosshair line) that appears on hover
rule = (
    base.mark_rule(color="gray", strokeWidth=1, strokeDash=[4, 4])
    .encode(opacity=alt.condition(nearest, alt.value(1), alt.value(0)))
    .add_params(nearest)
)

# Chart 1: Price
price_line = base.mark_line(color="#306998", strokeWidth=2).encode(
    y=alt.Y("price:Q", title="Price ($)", axis=alt.Axis(labelFontSize=14, titleFontSize=18))
)
price_points = base.mark_point(color="#306998", size=100).encode(
    y=alt.Y("price:Q"), opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)
price_text = base.mark_text(align="left", dx=10, dy=-10, fontSize=14, color="#306998").encode(
    y=alt.Y("price:Q"), text=alt.condition(nearest, alt.Text("price:Q", format="$.2f"), alt.value(""))
)
price_chart = alt.layer(price_line, price_points, price_text, rule).properties(
    width=1400, height=280, title=alt.Title("Price", fontSize=20, anchor="start")
)

# Chart 2: Volume
volume_bar = base.mark_bar(color="#FFD43B", opacity=0.7).encode(
    y=alt.Y("volume:Q", title="Volume", axis=alt.Axis(labelFontSize=14, titleFontSize=18, format="~s"))
)
volume_highlight = base.mark_bar(color="#FFD43B").encode(
    y=alt.Y("volume:Q"), opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)
volume_text = base.mark_text(align="left", dx=10, dy=-10, fontSize=14, color="#B8860B").encode(
    y=alt.Y("volume:Q"), text=alt.condition(nearest, alt.Text("volume:Q", format=",.0f"), alt.value(""))
)
volume_chart = alt.layer(volume_bar, volume_highlight, volume_text, rule).properties(
    width=1400, height=220, title=alt.Title("Volume", fontSize=20, anchor="start")
)

# Chart 3: Indicator
indicator_line = base.mark_line(color="#2E8B57", strokeWidth=2).encode(
    y=alt.Y(
        "indicator:Q",
        title="Momentum Indicator",
        scale=alt.Scale(domain=[0, 100]),
        axis=alt.Axis(labelFontSize=14, titleFontSize=18),
    )
)
indicator_points = base.mark_point(color="#2E8B57", size=100).encode(
    y=alt.Y("indicator:Q"), opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)
indicator_text = base.mark_text(align="left", dx=10, dy=-10, fontSize=14, color="#2E8B57").encode(
    y=alt.Y("indicator:Q"), text=alt.condition(nearest, alt.Text("indicator:Q", format=".1f"), alt.value(""))
)
# Reference lines for overbought/oversold levels
overbought = (
    alt.Chart(pd.DataFrame({"y": [70]})).mark_rule(color="red", strokeDash=[4, 4], strokeWidth=1).encode(y="y:Q")
)
oversold = (
    alt.Chart(pd.DataFrame({"y": [30]})).mark_rule(color="green", strokeDash=[4, 4], strokeWidth=1).encode(y="y:Q")
)
indicator_chart = alt.layer(indicator_line, indicator_points, indicator_text, overbought, oversold, rule).properties(
    width=1400, height=220, title=alt.Title("Momentum Indicator", fontSize=20, anchor="start")
)

# Combine charts vertically with shared x-axis
chart = (
    alt.vconcat(price_chart, volume_chart, indicator_chart, spacing=15)
    .properties(title=alt.Title("dashboard-synchronized-crosshair · altair · pyplots.ai", fontSize=28, anchor="middle"))
    .configure_axis(grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
