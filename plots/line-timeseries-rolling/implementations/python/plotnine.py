""" pyplots.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
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
    ggplot,
    guides,
    labs,
    scale_alpha_manual,
    scale_color_manual,
    scale_size_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Data - Daily temperature readings with 7-day rolling average
np.random.seed(42)

# Generate 180 days of temperature data (6 months)
dates = pd.date_range("2024-01-01", periods=180, freq="D")

# Create seasonal temperature pattern with noise
# Base seasonal pattern: winter -> spring -> summer
day_of_year = np.arange(180)
seasonal = 5 + 15 * np.sin(2 * np.pi * (day_of_year - 30) / 365)
noise = np.random.normal(0, 3, 180)
temperature = seasonal + noise

# Create DataFrame and calculate rolling average
df = pd.DataFrame({"date": dates, "temperature": temperature})
df["rolling_avg"] = df["temperature"].rolling(window=7, center=True).mean()

# Reshape data for plotnine - need long format for multiple series
df_raw = df[["date", "temperature"]].copy()
df_raw["series"] = "Daily Temperature"
df_raw = df_raw.rename(columns={"temperature": "value"})

df_roll = df[["date", "rolling_avg"]].dropna().copy()
df_roll["series"] = "7-Day Rolling Average"
df_roll = df_roll.rename(columns={"rolling_avg": "value"})

df_long = pd.concat([df_raw, df_roll], ignore_index=True)

# Make series categorical for consistent ordering
df_long["series"] = pd.Categorical(
    df_long["series"], categories=["Daily Temperature", "7-Day Rolling Average"], ordered=True
)

# Plot
plot = (
    ggplot(df_long, aes(x="date", y="value", color="series", alpha="series", size="series"))
    + geom_line()
    + scale_color_manual(values={"Daily Temperature": "#306998", "7-Day Rolling Average": "#FFD43B"})
    + scale_alpha_manual(values={"Daily Temperature": 0.5, "7-Day Rolling Average": 1.0})
    + scale_size_manual(values={"Daily Temperature": 0.8, "7-Day Rolling Average": 2.0})
    + guides(alpha="none", size="none")
    + scale_x_datetime(breaks=breaks_date(7), labels=label_date("%b %Y"))
    + labs(x="Date", y="Temperature (°C)", title="line-timeseries-rolling · plotnine · pyplots.ai", color="")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=30, hjust=1),
        legend_text=element_text(size=16),
        legend_title=element_text(size=0),
        legend_position="right",
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#dddddd", size=0.3, alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
