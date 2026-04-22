""" pyplots.ai
line-markers: Line Plot with Markers
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_shape_manual,
    theme,
    theme_minimal,
)


# Data: Monthly temperature readings from two weather stations
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Station A: Coastal location (milder temperatures)
station_a = np.array([8, 9, 12, 15, 19, 23, 26, 26, 22, 17, 12, 9]) + np.random.randn(12) * 0.5

# Station B: Inland location (more extreme temperatures)
station_b = np.array([2, 4, 10, 16, 21, 26, 29, 28, 22, 14, 7, 3]) + np.random.randn(12) * 0.5

df = pd.DataFrame(
    {
        "Month": month_labels * 2,
        "Month_Num": list(months) * 2,
        "Temperature": np.concatenate([station_a, station_b]),
        "Station": ["Coastal Station"] * 12 + ["Inland Station"] * 12,
    }
)

# Plot
plot = (
    ggplot(df, aes(x="Month_Num", y="Temperature", color="Station", shape="Station"))
    + geom_line(size=1.5, alpha=0.8)
    + geom_point(size=5, alpha=0.9)
    + scale_color_manual(values=["#306998", "#FFD43B"])
    + scale_shape_manual(values=["o", "s"])
    + labs(
        x="Month",
        y="Temperature (°C)",
        title="line-markers · plotnine · pyplots.ai",
        color="Weather Station",
        shape="Weather Station",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="right",
    )
)

plot.save("plot.png", dpi=300, verbose=False)
