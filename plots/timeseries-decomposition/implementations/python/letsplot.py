""" pyplots.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_line,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    ggtitle,
    labs,
    theme,
    theme_minimal,
)
from statsmodels.tsa.seasonal import seasonal_decompose


LetsPlot.setup_html()

# Data: Monthly temperature readings over 5 years (60 months)
np.random.seed(42)
n_months = 60
dates = pd.date_range("2019-01-01", periods=n_months, freq="MS")

# Create realistic temperature data with trend, seasonality, and noise
trend = np.linspace(15, 18, n_months)  # Gradual warming trend
seasonal = 12 * np.sin(2 * np.pi * np.arange(n_months) / 12)  # Annual cycle
noise = np.random.normal(0, 1.5, n_months)
values = trend + seasonal + noise

# Create DataFrame for decomposition
df_ts = pd.DataFrame({"date": dates, "value": values})
df_ts = df_ts.set_index("date")

# Perform seasonal decomposition (additive model)
decomposition = seasonal_decompose(df_ts["value"], model="additive", period=12)

# Extract components and create plotting DataFrames
df_original = pd.DataFrame({"date": dates, "value": values, "component": "Original"})

df_trend = pd.DataFrame({"date": dates, "value": decomposition.trend, "component": "Trend"})

df_seasonal = pd.DataFrame({"date": dates, "value": decomposition.seasonal, "component": "Seasonal"})

df_residual = pd.DataFrame({"date": dates, "value": decomposition.resid, "component": "Residual"})

# Combine all components
df_all = pd.concat([df_original, df_trend, df_seasonal, df_residual])

# Convert date to string for plotting
df_all["date_str"] = df_all["date"].dt.strftime("%Y-%m")

# Create individual plots for each component
colors = {"Original": "#306998", "Trend": "#DC2626", "Seasonal": "#059669", "Residual": "#7C3AED"}

# Plot 1: Original Series
p1 = (
    ggplot(df_original, aes(x="date", y="value"))
    + geom_line(color="#306998", size=1.2)
    + labs(x="", y="Temperature (°C)", title="Original Series")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=20, face="bold"),
        axis_title=element_text(size=16),
        axis_text=element_text(size=14),
        axis_text_x=element_blank(),
    )
    + ggsize(1600, 200)
)

# Plot 2: Trend Component
p2 = (
    ggplot(df_trend.dropna(), aes(x="date", y="value"))
    + geom_line(color="#DC2626", size=1.2)
    + labs(x="", y="Temperature (°C)", title="Trend")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=20, face="bold"),
        axis_title=element_text(size=16),
        axis_text=element_text(size=14),
        axis_text_x=element_blank(),
    )
    + ggsize(1600, 200)
)

# Plot 3: Seasonal Component
p3 = (
    ggplot(df_seasonal, aes(x="date", y="value"))
    + geom_line(color="#059669", size=1.2)
    + labs(x="", y="Temperature (°C)", title="Seasonal")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=20, face="bold"),
        axis_title=element_text(size=16),
        axis_text=element_text(size=14),
        axis_text_x=element_blank(),
    )
    + ggsize(1600, 200)
)

# Plot 4: Residual Component
p4 = (
    ggplot(df_residual.dropna(), aes(x="date", y="value"))
    + geom_line(color="#7C3AED", size=1.2)
    + labs(x="Date", y="Temperature (°C)", title="Residual")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=20, face="bold"),
        axis_title=element_text(size=16),
        axis_text=element_text(size=14),
        axis_text_x=element_text(angle=45),
    )
    + ggsize(1600, 200)
)

# Create combined plot using gggrid
combined = gggrid([p1, p2, p3, p4], ncol=1)

# Add overall title
final_plot = (
    combined
    + ggsize(1600, 900)
    + ggtitle("timeseries-decomposition · letsplot · pyplots.ai")
    + theme(plot_title=element_text(size=24, face="bold"))
)

# Save as PNG with scale for 4800x2700 resolution
ggsave(final_plot, "plot.png", scale=3)

# Save HTML for interactive version
ggsave(final_plot, "plot.html")

# Move files from lets-plot subdirectory to current directory
lp_dir = "lets-plot-images"
if os.path.exists(lp_dir):
    for f in ["plot.png", "plot.html"]:
        src = os.path.join(lp_dir, f)
        if os.path.exists(src):
            shutil.move(src, f)
    os.rmdir(lp_dir)
