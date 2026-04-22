""" pyplots.ai
indicator-rsi: RSI Technical Indicator Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_text,
    geom_hline,
    geom_line,
    ggplot,
    labs,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Generate RSI values for 120 trading days
np.random.seed(42)
n_days = 120
period = 14

# Generate synthetic price changes to calculate RSI
price_changes = np.random.normal(0, 1.5, n_days + period)

# Calculate RSI using 14-period lookback (inline calculation)
rsi_values = []
for i in range(period, len(price_changes)):
    window = price_changes[i - period : i]
    gains = np.maximum(window, 0)
    losses = np.abs(np.minimum(window, 0))
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    rsi_values.append(rsi)
rsi_values = np.array(rsi_values)

# Create date range (business days)
dates = pd.date_range(start="2024-01-01", periods=n_days, freq="B")

df = pd.DataFrame({"date": dates, "rsi": rsi_values})

# Plot
plot = (
    ggplot(df, aes(x="date", y="rsi"))
    # Overbought zone (70-100) - light red shading
    + annotate("rect", xmin=dates.min(), xmax=dates.max(), ymin=70, ymax=100, fill="#FF6B6B", alpha=0.2)
    # Oversold zone (0-30) - light green shading
    + annotate("rect", xmin=dates.min(), xmax=dates.max(), ymin=0, ymax=30, fill="#4ECDC4", alpha=0.2)
    # Threshold lines
    + geom_hline(yintercept=70, color="#D62828", size=1, linetype="dashed", alpha=0.8)
    + geom_hline(yintercept=30, color="#2A9D8F", size=1, linetype="dashed", alpha=0.8)
    + geom_hline(yintercept=50, color="#6C757D", size=0.8, linetype="dotted", alpha=0.6)
    # RSI line
    + geom_line(color="#306998", size=1.5, alpha=0.9)
    # Axis settings
    + scale_y_continuous(limits=(0, 100), breaks=range(0, 101, 10))
    + scale_x_datetime(date_breaks="1 month", date_labels="%b %Y")
    # Labels
    + labs(title="indicator-rsi · plotnine · pyplots.ai", x="Date", y="RSI (14-period)")
    # Theme
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=0, ha="center"),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_text(color="#E0E0E0"),
    )
)

# Save
plot.save("plot.png", dpi=300, width=16, height=9)
