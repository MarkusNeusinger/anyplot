""" pyplots.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 88/100 | Created: 2026-04-12
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    facet_wrap,
    geom_abline,
    geom_point,
    ggplot,
    labs,
    scale_color_gradient,
    theme,
    theme_minimal,
)


# Data - Daily temperature with natural autocorrelation (AR(1) process)
np.random.seed(42)
n = 300
phi = 0.85
noise = np.random.normal(0, 2.5, n)
temperatures = np.zeros(n)
temperatures[0] = 20 + noise[0]
for i in range(1, n):
    temperatures[i] = (1 - phi) * 20 + phi * temperatures[i - 1] + noise[i]

# Create lag data for multiple lag values
lags = [1, 3, 7]
rows = []
for lag in lags:
    for i in range(n - lag):
        rows.append(
            {
                "temp_t": temperatures[i],
                "temp_t_lag": temperatures[i + lag],
                "day": i,
                "lag": f"Lag = {lag} day{'s' if lag > 1 else ''}",
            }
        )
df = pd.DataFrame(rows)
df["lag"] = pd.Categorical(df["lag"], categories=[f"Lag = {k} day{'s' if k > 1 else ''}" for k in lags], ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="temp_t", y="temp_t_lag", color="day"))
    + geom_abline(intercept=0, slope=1, color="#BBBBBB", linetype="dashed", size=0.7)
    + geom_point(size=3, alpha=0.65)
    + facet_wrap("lag", ncol=3)
    + scale_color_gradient(low="#306998", high="#E8A838", name="Day")
    + labs(
        x="Temperature at Day t (°C)",
        y="Temperature at Day t+k (°C)",
        title="Daily Temperature · scatter-lag · plotnine · pyplots.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        strip_text=element_text(size=18, weight="bold"),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        panel_grid_major=element_line(color="#E8E8E8", size=0.5),
        panel_grid_minor=element_blank(),
        axis_ticks=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300)
