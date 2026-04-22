""" pyplots.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_text,
    geom_line,
    geom_ribbon,
    ggplot,
    ggsize,
    labs,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Generate synthetic stock price data with Bollinger Bands
np.random.seed(42)
n_periods = 120

# Generate price data with trend and volatility
dates = pd.date_range(start="2024-01-01", periods=n_periods, freq="B")
returns = np.random.normal(0.0005, 0.018, n_periods)
# Add some volatility clustering
volatility_multiplier = np.where((np.arange(n_periods) > 40) & (np.arange(n_periods) < 70), 1.8, 1.0)
returns = returns * volatility_multiplier
close = 100 * np.exp(np.cumsum(returns))

# Calculate Bollinger Bands (20-period SMA with 2 standard deviations)
window = 20
sma = pd.Series(close).rolling(window=window).mean().values
std = pd.Series(close).rolling(window=window).std().values
upper_band = sma + 2 * std
lower_band = sma - 2 * std

df = pd.DataFrame({"date": dates, "close": close, "sma": sma, "upper_band": upper_band, "lower_band": lower_band})

# Remove NaN values from rolling calculations
df = df.dropna().reset_index(drop=True)

# Create plot
plot = (
    ggplot(df)
    # Bollinger Bands fill area (between upper and lower bands)
    + geom_ribbon(aes(x="date", ymin="lower_band", ymax="upper_band"), fill="#306998", alpha=0.2)
    # Lower band line
    + geom_line(aes(x="date", y="lower_band"), color="#306998", size=1.0, alpha=0.7)
    # Upper band line
    + geom_line(aes(x="date", y="upper_band"), color="#306998", size=1.0, alpha=0.7)
    # Middle band (SMA) - dashed line
    + geom_line(aes(x="date", y="sma"), color="#306998", size=1.2, linetype="dashed", alpha=0.9)
    # Close price line - prominent
    + geom_line(aes(x="date", y="close"), color="#FFD43B", size=1.8)
    # Labels
    + labs(title="indicator-bollinger \u00b7 letsplot \u00b7 pyplots.ai", x="Date", y="Price (USD)")
    # Theme and styling
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid=element_line(color="#cccccc", size=0.5),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, "plot.html", path=".")
