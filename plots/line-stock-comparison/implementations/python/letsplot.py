""" pyplots.ai
line-stock-comparison: Stock Price Comparison Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Generate synthetic stock prices for AAPL, GOOGL, MSFT, and SPY
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=252, freq="B")  # ~1 year trading days
symbols = ["AAPL", "GOOGL", "MSFT", "SPY"]

# Generate realistic stock price movements using geometric Brownian motion
data_frames = []
for symbol in symbols:
    # Different drift and volatility for each stock
    if symbol == "AAPL":
        drift, volatility = 0.0008, 0.018
    elif symbol == "GOOGL":
        drift, volatility = 0.0006, 0.020
    elif symbol == "MSFT":
        drift, volatility = 0.0009, 0.016
    else:  # SPY (index - lower volatility)
        drift, volatility = 0.0005, 0.010

    returns = np.random.normal(drift, volatility, len(dates))
    price = 100 * np.exp(np.cumsum(returns))  # Start at 100 for simplicity

    df_symbol = pd.DataFrame({"date": dates, "symbol": symbol, "price": price})
    data_frames.append(df_symbol)

df = pd.concat(data_frames, ignore_index=True)

# Normalize prices to 100 at start (rebase)
df["rebased"] = df.groupby("symbol")["price"].transform(lambda x: x / x.iloc[0] * 100)

# Convert to day numbers for x-axis (lets-plot handles this better)
df["day"] = df.groupby("symbol").cumcount() + 1

# Plot
plot = (
    ggplot(df, aes(x="day", y="rebased", color="symbol"))  # noqa: F405
    + geom_line(size=1.5, alpha=0.9)  # noqa: F405
    + geom_hline(yintercept=100, linetype="dashed", color="#666666", size=0.8, alpha=0.7)  # noqa: F405
    + scale_color_manual(  # noqa: F405
        values=["#306998", "#FFD43B", "#DC2626", "#22C55E"], name="Symbol"
    )
    + labs(  # noqa: F405
        title="line-stock-comparison · letsplot · pyplots.ai", x="Trading Day", y="Rebased Price (Start = 100)"
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, face="bold"),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        legend_title=element_text(size=18),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
        legend_position="right",
        panel_grid_major=element_line(color="#E5E5E5", size=0.5),  # noqa: F405
        panel_grid_minor=element_line(color="#F5F5F5", size=0.3),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename="plot.html", path=".")
