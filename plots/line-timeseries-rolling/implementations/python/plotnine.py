""" anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
import plotnine as pn
from mizani.breaks import breaks_date
from mizani.labels import label_date


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD"]  # brand green, vermillion

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
    pn.ggplot(df_long, pn.aes(x="date", y="value", color="series", alpha="series", size="series"))
    + pn.geom_line()
    + pn.scale_color_manual(values={"Daily Temperature": IMPRINT[0], "7-Day Rolling Average": IMPRINT[1]})
    + pn.scale_alpha_manual(values={"Daily Temperature": 0.5, "7-Day Rolling Average": 1.0})
    + pn.scale_size_manual(values={"Daily Temperature": 0.8, "7-Day Rolling Average": 2.0})
    + pn.guides(alpha="none", size="none")
    + pn.scale_x_datetime(breaks=breaks_date(14), labels=label_date("%b %Y"))
    + pn.labs(x="Date", y="Temperature (°C)", title="line-timeseries-rolling · plotnine · anyplot.ai", color="")
    + pn.theme_minimal()
    + pn.theme(
        figure_size=(16, 9),
        plot_background=pn.element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=pn.element_rect(fill=PAGE_BG),
        panel_grid_major=pn.element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=pn.element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=pn.element_rect(color=INK_SOFT, fill=None),
        axis_title=pn.element_text(size=20, color=INK),
        axis_text=pn.element_text(size=16, color=INK_SOFT),
        axis_text_x=pn.element_text(angle=30, hjust=1),
        axis_line=pn.element_line(color=INK_SOFT),
        plot_title=pn.element_text(size=24, color=INK),
        legend_background=pn.element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=pn.element_text(size=16, color=INK_SOFT),
        legend_title=pn.element_text(size=0),
        legend_position="right",
        text=pn.element_text(size=14),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
