""" pyplots.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Data - Generate realistic stock price data with trend and volatility
np.random.seed(42)
n_days = 300
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")  # Business days

# Create a price series with trends and mean reversion
base_price = 150
returns = np.random.normal(0.0003, 0.015, n_days)  # Daily returns
# Add some trending behavior
trend = np.sin(np.linspace(0, 3 * np.pi, n_days)) * 0.001
returns = returns + trend
close = base_price * np.cumprod(1 + returns)

# Calculate SMAs
df = pd.DataFrame({"date": dates, "close": close})
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Reshape data for plotnine (long format for multiple lines with legend)
df_long = pd.melt(
    df, id_vars=["date"], value_vars=["close", "sma_20", "sma_50", "sma_200"], var_name="series", value_name="price"
)

# Rename series for legend
series_labels = {"close": "Price", "sma_20": "SMA 20", "sma_50": "SMA 50", "sma_200": "SMA 200"}
df_long["series"] = df_long["series"].map(series_labels)

# Set order for legend
series_order = ["Price", "SMA 20", "SMA 50", "SMA 200"]
df_long["series"] = pd.Categorical(df_long["series"], categories=series_order, ordered=True)

# Define colors matching the other implementations
colors = {"Price": "#306998", "SMA 20": "#FFD43B", "SMA 50": "#E74C3C", "SMA 200": "#2ECC71"}

# Plot
plot = (
    ggplot(df_long, aes(x="date", y="price", color="series"))
    + geom_line(size=1.5, alpha=0.9)
    + scale_color_manual(values=colors)
    + scale_x_datetime(date_breaks="2 months", date_labels="%b %Y")
    + labs(x="Date", y="Price ($)", title="indicator-sma · plotnine · pyplots.ai", color="")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(rotation=30, ha="right"),
        legend_text=element_text(size=16),
        legend_position=(0.02, 0.98),
        legend_direction="vertical",
        panel_grid_major_y=element_line(color="#cccccc", size=0.5, alpha=0.3),
        panel_grid_major_x=element_line(alpha=0),
        panel_grid_minor=element_line(alpha=0),
    )
)

plot.save("plot.png", dpi=300)
