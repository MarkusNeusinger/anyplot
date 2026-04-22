""" pyplots.ai
line-timeseries: Time Series Line Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Daily temperature readings over one year
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=365, freq="D")

# Simulate realistic temperature data with seasonal pattern
day_of_year = np.arange(365)
seasonal_pattern = 15 * np.sin(2 * np.pi * (day_of_year - 80) / 365)  # Peak in summer
baseline = 12  # Average temperature
noise = np.random.randn(365) * 3  # Daily variation
temperature = baseline + seasonal_pattern + noise

df = pd.DataFrame({"date": dates, "temperature": temperature})

# Create plot
plot = (
    ggplot(df, aes(x="date", y="temperature"))
    + geom_line(color="#306998", size=1.5, alpha=0.9)
    + labs(x="Date", y="Temperature (°C)", title="line-timeseries · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=45),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_line(color="#EEEEEE", size=0.3),
    )
    + ggsize(1600, 900)
    + scale_x_datetime(format="%b %Y")
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
