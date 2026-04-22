""" pyplots.ai
subplot-grid: Subplot Grid Layout
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Financial dashboard theme
np.random.seed(42)

# Generate 60 days of stock-like data
days = 60
day_nums = np.arange(days)

# Price data (cumulative random walk)
returns = np.random.normal(0.001, 0.02, days)
price = 100 * np.cumprod(1 + returns)

# Volume data (random with some correlation to price moves)
base_volume = 1_000_000
volume = base_volume * (1 + 0.5 * np.abs(returns) / 0.02 + np.random.uniform(0, 0.5, days))

# Daily returns for histogram
daily_returns = np.diff(np.log(price)) * 100  # Log returns as percentage

# Create DataFrames for each subplot
price_df = pd.DataFrame({"day": day_nums, "price": price})
volume_df = pd.DataFrame({"day": day_nums, "volume": volume / 1_000_000})  # In millions
returns_df = pd.DataFrame({"return": daily_returns})

# Rolling 10-day average for price
price_df["rolling_avg"] = pd.Series(price).rolling(window=10, min_periods=1).mean()

# Create individual plots

# Top left: Price line chart
price_plot = (
    ggplot(price_df, aes(x="day", y="price"))
    + geom_line(color="#306998", size=1.5)
    + geom_line(aes(y="rolling_avg"), color="#FFD43B", size=1.2, linetype="dashed")
    + labs(x="Trading Day", y="Price ($)", title="Stock Price with 10-Day Moving Average")
    + theme_minimal()
    + theme(axis_title=element_text(size=18), axis_text=element_text(size=14), plot_title=element_text(size=20))
)

# Top right: Volume bar chart
volume_plot = (
    ggplot(volume_df, aes(x="day", y="volume"))
    + geom_bar(stat="identity", fill="#306998", alpha=0.7, width=0.8)
    + labs(x="Trading Day", y="Volume (Millions)", title="Daily Trading Volume")
    + theme_minimal()
    + theme(axis_title=element_text(size=18), axis_text=element_text(size=14), plot_title=element_text(size=20))
)

# Bottom left: Returns histogram
returns_plot = (
    ggplot(returns_df, aes(x="return"))
    + geom_histogram(fill="#306998", color="#1a3a52", bins=20, alpha=0.8)
    + geom_vline(xintercept=0, color="#FFD43B", size=1.5, linetype="dashed")
    + labs(x="Daily Return (%)", y="Frequency", title="Distribution of Daily Returns")
    + theme_minimal()
    + theme(axis_title=element_text(size=18), axis_text=element_text(size=14), plot_title=element_text(size=20))
)

# Bottom right: Scatter plot - price vs volume relationship
scatter_df = pd.DataFrame({"abs_return": np.abs(daily_returns), "volume": volume[1:] / 1_000_000})
scatter_plot = (
    ggplot(scatter_df, aes(x="abs_return", y="volume"))
    + geom_point(color="#306998", size=4, alpha=0.7)
    + geom_smooth(method="lm", color="#FFD43B", size=1.5)
    + labs(x="Absolute Return (%)", y="Volume (Millions)", title="Volume vs Price Movement")
    + theme_minimal()
    + theme(axis_title=element_text(size=18), axis_text=element_text(size=14), plot_title=element_text(size=20))
)

# Combine into 2x2 grid using gggrid
grid_plot = gggrid([price_plot, volume_plot, returns_plot, scatter_plot], ncol=2)

# Add overall title
final_plot = (
    grid_plot
    + ggsize(1600, 900)
    + ggtitle("subplot-grid · lets-plot · pyplots.ai")
    + theme(plot_title=element_text(size=28))
)

# Save as PNG (scale=3 for 4800x2700, path='.' to save in current directory)
ggsave(final_plot, "plot.png", path=".", scale=3)

# Also save as HTML for interactive version
ggsave(final_plot, "plot.html", path=".")
