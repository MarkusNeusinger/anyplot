""" pyplots.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Data - Generate synthetic stock price data with EMAs
np.random.seed(42)

# Generate 120 trading days
n_days = 120
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Generate realistic stock price using random walk with drift
initial_price = 150.0
returns = np.random.normal(0.0008, 0.018, n_days)
price = initial_price * np.cumprod(1 + returns)

# Calculate EMAs using pandas ewm
ema_12 = pd.Series(price).ewm(span=12, adjust=False).mean().values
ema_26 = pd.Series(price).ewm(span=26, adjust=False).mean().values

# Create long-format DataFrame for plotnine
df_price = pd.DataFrame({"date": dates, "value": price, "series": "Close Price"})
df_ema12 = pd.DataFrame({"date": dates, "value": ema_12, "series": "EMA-12"})
df_ema26 = pd.DataFrame({"date": dates, "value": ema_26, "series": "EMA-26"})
df = pd.concat([df_price, df_ema12, df_ema26], ignore_index=True)

# Define colors - Python Blue for price, distinct colors for EMAs
colors = {"Close Price": "#306998", "EMA-12": "#E24A33", "EMA-26": "#FFD43B"}

# Find crossover points (where EMA-12 crosses EMA-26)
crossover_indices = []
for i in range(1, len(ema_12)):
    if (ema_12[i - 1] <= ema_26[i - 1] and ema_12[i] > ema_26[i]) or (
        ema_12[i - 1] >= ema_26[i - 1] and ema_12[i] < ema_26[i]
    ):
        crossover_indices.append(i)

df_crossovers = pd.DataFrame({"date": dates[crossover_indices], "value": ema_12[crossover_indices]})

# Plot
plot = (
    ggplot(df, aes(x="date", y="value", color="series"))
    + geom_line(data=df[df["series"] == "Close Price"], size=1.8, alpha=0.9)
    + geom_line(data=df[df["series"] == "EMA-12"], size=1.2, alpha=0.85)
    + geom_line(data=df[df["series"] == "EMA-26"], size=1.2, alpha=0.85)
    + geom_point(df_crossovers, aes(x="date", y="value"), color="#2CA02C", size=5, alpha=1.0, inherit_aes=False)
    + scale_color_manual(values=colors)
    + scale_x_datetime(date_breaks="1 month", date_labels="%b %Y")
    + labs(title="indicator-ema \u00b7 plotnine \u00b7 pyplots.ai", x="Date", y="Price ($)", color="Series")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=45, ha="right"),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        legend_background=element_rect(fill="white", alpha=0.8),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
