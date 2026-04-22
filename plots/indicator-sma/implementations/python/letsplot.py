""" pyplots.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_line,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Generate synthetic stock price data
np.random.seed(42)
n_periods = 300

# Create date range (approx 1 year of trading days)
dates = pd.date_range(start="2024-01-02", periods=n_periods, freq="B")

# Generate price data with trend and noise
returns = np.random.normal(0.0005, 0.015, n_periods)
price_series = 100 * np.cumprod(1 + returns)

# Calculate SMAs
sma_20 = pd.Series(price_series).rolling(window=20).mean()
sma_50 = pd.Series(price_series).rolling(window=50).mean()
sma_200 = pd.Series(price_series).rolling(window=200).mean()

# Create DataFrame
df = pd.DataFrame({"date": dates, "Close": price_series, "SMA 20": sma_20, "SMA 50": sma_50, "SMA 200": sma_200})

# Melt for plotting multiple lines
df_long = df.melt(
    id_vars=["date"], value_vars=["Close", "SMA 20", "SMA 50", "SMA 200"], var_name="series", value_name="price"
)

# Define colors: Python Blue for close, then distinct colors for SMAs
colors = {"Close": "#306998", "SMA 20": "#FFD43B", "SMA 50": "#22C55E", "SMA 200": "#DC2626"}

# Create plot
plot = (
    ggplot(df_long, aes(x="date", y="price", color="series"))
    + geom_line(size=1.2)
    + scale_color_manual(values=colors)
    + scale_x_datetime()
    + labs(title="indicator-sma \u00b7 letsplot \u00b7 pyplots.ai", x="Date", y="Price (USD)", color="Series")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, "plot.html", path=".")
