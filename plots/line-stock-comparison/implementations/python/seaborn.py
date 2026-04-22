""" pyplots.ai
line-stock-comparison: Stock Price Comparison Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Generate synthetic stock price data for 4 tech companies over 1 year
np.random.seed(42)

dates = pd.date_range("2024-01-01", periods=252, freq="B")  # Business days
symbols = ["AAPL", "GOOGL", "MSFT", "SPY"]

# Generate realistic stock price movements using geometric Brownian motion
data = []
for symbol in symbols:
    # Different drift and volatility for each stock
    if symbol == "AAPL":
        drift, volatility = 0.0008, 0.018
    elif symbol == "GOOGL":
        drift, volatility = 0.0006, 0.022
    elif symbol == "MSFT":
        drift, volatility = 0.0010, 0.016
    else:  # SPY (index, lower volatility)
        drift, volatility = 0.0005, 0.010

    returns = np.random.normal(drift, volatility, len(dates))
    price = 100 * np.exp(np.cumsum(returns))  # Start at 100 (already rebased)

    for date, p in zip(dates, price, strict=True):
        data.append({"date": date, "symbol": symbol, "rebased_price": p})

df = pd.DataFrame(data)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Set seaborn style
sns.set_style("whitegrid")

# Use distinct, colorblind-safe colors
palette = {"AAPL": "#306998", "GOOGL": "#E24A33", "MSFT": "#8EBA42", "SPY": "#FFD43B"}

# Line plot with distinct colors
sns.lineplot(data=df, x="date", y="rebased_price", hue="symbol", palette=palette, linewidth=2.5, ax=ax)

# Add reference line at 100 (starting point)
ax.axhline(y=100, color="gray", linestyle="--", linewidth=1.5, alpha=0.7, label="_nolegend_")

# Styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Rebased Price (Start = 100)", fontsize=20)
ax.set_title("line-stock-comparison · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Improve legend
ax.legend(title="Symbol", fontsize=16, title_fontsize=18, loc="upper left")

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
