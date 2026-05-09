""" anyplot.ai
line-timeseries: Time Series Line Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-09
"""

import os
import sys


# Remove the current directory from sys.path to avoid importing altair.py
sys.path = [p for p in sys.path if p != "" and not p.endswith("python")]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

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
    .mark_line(strokeWidth=3, color=BRAND, point=True, size=150)
    .encode(
        x=alt.X(
            "date:T",
            title="Date",
            axis=alt.Axis(
                format="%b %Y",
                labelFontSize=18,
                titleFontSize=22,
                labelAngle=-45,
                tickCount=12,
                labelColor=INK_SOFT,
                titleColor=INK,
                domainColor=INK_SOFT,
                gridColor=INK,
                gridOpacity=0.10,
            ),
        ),
        y=alt.Y(
            "price:Q",
            title="Stock Price ($)",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(
                labelFontSize=18,
                titleFontSize=22,
                labelColor=INK_SOFT,
                titleColor=INK,
                domainColor=INK_SOFT,
                gridColor=INK,
                gridOpacity=0.10,
            ),
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%B %d, %Y"),
            alt.Tooltip("price:Q", title="Price", format="$.2f"),
        ],
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("line-timeseries · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=1)
    .configure_title(color=INK, fontSize=28)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .interactive()
)

# Save outputs
script_dir = os.path.dirname(os.path.abspath(__file__))
chart.save(os.path.join(script_dir, f"plot-{THEME}.png"), scale_factor=3.0)
chart.save(os.path.join(script_dir, f"plot-{THEME}.html"))
