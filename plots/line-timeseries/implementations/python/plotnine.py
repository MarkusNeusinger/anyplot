""" pyplots.ai
line-timeseries: Time Series Line Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from mizani.breaks import breaks_date
from mizani.labels import label_date
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Data: Daily stock prices over one year
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=252, freq="B")  # Business days
price = 100.0
prices = []
for _ in range(252):
    price = price * (1 + np.random.randn() * 0.015)
    prices.append(price)

df = pd.DataFrame({"date": dates, "price": prices})

# Plot
plot = (
    ggplot(df, aes(x="date", y="price"))
    + geom_line(color="#306998", size=1.5, alpha=0.9)
    + geom_point(color="#306998", size=0.8, alpha=0.5)
    + scale_x_datetime(breaks=breaks_date(7), labels=label_date("%b %Y"))
    + labs(title="line-timeseries · plotnine · pyplots.ai", x="Date", y="Stock Price ($)")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=45, hjust=1),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#dddddd", size=0.3, alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300)
