""" pyplots.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Generate realistic stock price data with EMA indicators
np.random.seed(42)

# Create 120 trading days
dates = pd.date_range("2024-01-02", periods=120, freq="B")

# Generate price data with trend and noise
returns = np.random.normal(0.001, 0.015, 120)
price = 100 * np.cumprod(1 + returns)

# Calculate EMA using pandas ewm (exponential weighted mean)
price_series = pd.Series(price)
ema_12 = price_series.ewm(span=12, adjust=False).mean().values
ema_26 = price_series.ewm(span=26, adjust=False).mean().values

# Create DataFrame
df = pd.DataFrame({"date": dates, "date_num": range(len(dates)), "close": price, "ema_12": ema_12, "ema_26": ema_26})

# Reshape for plotting with lets-plot (long format)
df_price = df[["date_num", "close"]].copy()
df_price["series"] = "Close Price"
df_price = df_price.rename(columns={"close": "value"})

df_ema12 = df[["date_num", "ema_12"]].copy()
df_ema12["series"] = "EMA 12"
df_ema12 = df_ema12.rename(columns={"ema_12": "value"})

df_ema26 = df[["date_num", "ema_26"]].copy()
df_ema26["series"] = "EMA 26"
df_ema26 = df_ema26.rename(columns={"ema_26": "value"})

df_long = pd.concat([df_price, df_ema12, df_ema26], ignore_index=True)

# Create x-axis labels (show every 20th date)
date_labels = {i: dates[i].strftime("%b %d") for i in range(0, 120, 20)}

# Plot
plot = (
    ggplot(df_long, aes(x="date_num", y="value", color="series"))  # noqa: F405
    + geom_line(aes(size="series"))  # noqa: F405
    + scale_color_manual(values=["#306998", "#FFD43B", "#DC2626"], name="Series")  # noqa: F405
    + scale_size_manual(values=[2.5, 1.5, 1.5], name="Series")  # noqa: F405
    + scale_x_continuous(  # noqa: F405
        breaks=list(date_labels.keys()), labels=list(date_labels.values())
    )
    + labs(  # noqa: F405
        x="Date", y="Price (USD)", title="indicator-ema · letsplot · pyplots.ai"
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
        legend_title=element_text(size=18),  # noqa: F405
        legend_position="right",
        panel_grid=element_line(color="#CCCCCC", size=0.5, linetype="dashed"),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, "plot.html", path=".")
