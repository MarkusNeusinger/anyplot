""" pyplots.ai
indicator-macd: MACD Technical Indicator Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Generate realistic stock price data
np.random.seed(42)
n_days = 120

# Simulate stock prices with trend and volatility
dates = pd.date_range(start="2024-01-01", periods=n_days + 35, freq="B")  # Extra days for EMA calc
returns = np.random.normal(0.0005, 0.02, n_days + 35)
# Add some trending behavior
trend = np.sin(np.linspace(0, 4 * np.pi, n_days + 35)) * 0.01
returns = returns + trend
prices = 100 * np.cumprod(1 + returns)

# Calculate EMAs using pandas ewm
ema_12 = pd.Series(prices).ewm(span=12, adjust=False).mean().values
ema_26 = pd.Series(prices).ewm(span=26, adjust=False).mean().values

# Calculate MACD components
macd_line = ema_12 - ema_26
signal_line = pd.Series(macd_line).ewm(span=9, adjust=False).mean().values
histogram = macd_line - signal_line

# Use the last n_days (after warmup period)
start_idx = 35
df = pd.DataFrame(
    {
        "date": dates[start_idx:],
        "macd": macd_line[start_idx:],
        "signal": signal_line[start_idx:],
        "histogram": histogram[start_idx:],
    }
)

# Convert dates to numeric for plotting
df["day_num"] = range(len(df))
df["hist_color"] = np.where(df["histogram"] >= 0, "Positive", "Negative")

# Create separate dataframes for lines
df_lines = pd.melt(
    df[["day_num", "macd", "signal"]],
    id_vars=["day_num"],
    value_vars=["macd", "signal"],
    var_name="line_type",
    value_name="value",
)
df_lines["line_type"] = df_lines["line_type"].map({"macd": "MACD Line", "signal": "Signal Line"})

# Create the MACD chart
plot = (
    ggplot()
    # Histogram bars
    + geom_bar(
        data=df, mapping=aes(x="day_num", y="histogram", fill="hist_color"), stat="identity", width=0.8, alpha=0.8
    )
    # Zero reference line
    + geom_hline(yintercept=0, color="#666666", size=0.8, linetype="dashed")
    # MACD and Signal lines
    + geom_line(data=df_lines, mapping=aes(x="day_num", y="value", color="line_type"), size=1.5)
    # Manual color scales
    + scale_fill_manual(values={"Positive": "#22C55E", "Negative": "#EF4444"}, name="Histogram")
    + scale_color_manual(values={"MACD Line": "#306998", "Signal Line": "#FFD43B"}, name="Lines")
    # Labels and title
    + labs(x="Trading Day", y="MACD Value", title="indicator-macd · letsplot · pyplots.ai")
    # Theme styling
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale=3 gives 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML version
ggsave(plot, "plot.html", path=".")
