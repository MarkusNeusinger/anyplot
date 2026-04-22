""" pyplots.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_line,
    geom_ribbon,
    ggplot,
    labs,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Data - Generate realistic stock price with Bollinger Bands
np.random.seed(42)
n_periods = 120
dates = pd.date_range("2024-01-01", periods=n_periods, freq="B")  # Business days

# Generate price with trend and volatility
returns = np.random.normal(0.001, 0.018, n_periods)
price = 100 * np.cumprod(1 + returns)

# Add some volatility clusters for interesting band patterns
volatility_shock = np.zeros(n_periods)
volatility_shock[30:45] = np.random.normal(0, 0.025, 15)  # High volatility period
volatility_shock[80:95] = np.random.normal(0, 0.02, 15)  # Another volatile period
price = price * (1 + volatility_shock)

# Calculate Bollinger Bands (20-period SMA, 2 standard deviations)
window = 20
sma = pd.Series(price).rolling(window=window).mean()
std = pd.Series(price).rolling(window=window).std()
upper_band = sma + 2 * std
lower_band = sma - 2 * std

# Create DataFrame
df = pd.DataFrame({"date": dates, "close": price, "sma": sma, "upper_band": upper_band, "lower_band": lower_band})

# Remove NaN values from rolling calculation
df = df.dropna().reset_index(drop=True)

# Create long format for lines
df_lines = pd.melt(
    df, id_vars=["date", "upper_band", "lower_band"], value_vars=["close", "sma"], var_name="series", value_name="value"
)
df_lines["series"] = df_lines["series"].replace({"close": "Close Price", "sma": "20-Day SMA"})

# Plot
plot = (
    ggplot(df)
    + geom_ribbon(aes(x="date", ymin="lower_band", ymax="upper_band"), fill="#306998", alpha=0.2)
    + geom_line(aes(x="date", y="upper_band"), color="#306998", size=0.8, linetype="dashed")
    + geom_line(aes(x="date", y="lower_band"), color="#306998", size=0.8, linetype="dashed")
    + geom_line(
        data=df_lines[df_lines["series"] == "20-Day SMA"],
        mapping=aes(x="date", y="value"),
        color="#306998",
        size=1.0,
        linetype="dotted",
    )
    + geom_line(
        data=df_lines[df_lines["series"] == "Close Price"], mapping=aes(x="date", y="value"), color="#FFD43B", size=1.2
    )
    + scale_x_datetime(date_labels="%b %Y", date_breaks="1 month")
    + labs(x="Date", y="Price (USD)", title="indicator-bollinger · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=45, ha="right"),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(color="#cccccc", size=0.3, alpha=0.3),
        panel_grid_minor=element_line(color="#eeeeee", size=0.2, alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
