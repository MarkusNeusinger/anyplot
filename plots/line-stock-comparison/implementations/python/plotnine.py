""" pyplots.ai
line-stock-comparison: Stock Price Comparison Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_hline,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_date,
    theme,
    theme_minimal,
)


# Data - Generate synthetic stock price data for comparison
np.random.seed(42)
n_days = 252  # One year of trading days
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")  # Business days

# Create price series with different drift and volatility
symbols = ["AAPL", "GOOGL", "MSFT", "SPY"]
colors = ["#306998", "#FFD43B", "#E74C3C", "#2ECC71"]  # Python blue/yellow first

dfs = []
for symbol in symbols:
    # Random walk with drift
    daily_returns = np.random.normal(0.0004, 0.015, n_days)
    prices = 100 * np.exp(np.cumsum(daily_returns))  # Start at 100 (already rebased)
    dfs.append(pd.DataFrame({"date": dates, "symbol": symbol, "rebased": prices}))

df = pd.concat(dfs, ignore_index=True)

# Create plot
plot = (
    ggplot(df, aes(x="date", y="rebased", color="symbol"))
    + geom_hline(yintercept=100, linetype="dashed", color="#888888", size=0.8)
    + geom_line(size=1.5)
    + scale_color_manual(values=colors)
    + scale_x_date(date_labels="%b %Y", date_breaks="2 months")
    + labs(
        x="Date",
        y="Rebased Price (Starting = 100)",
        title="line-stock-comparison · plotnine · pyplots.ai",
        color="Symbol",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=45, ha="right"),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_line(color="#EEEEEE", size=0.3),
    )
)

# Save
plot.save("plot.png", dpi=300)
