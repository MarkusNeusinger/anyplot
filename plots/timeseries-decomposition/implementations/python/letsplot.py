""" anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-14
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    ggtitle,
    labs,
    theme,
)
from statsmodels.tsa.seasonal import seasonal_decompose


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for components
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

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

# Create individual plots for each component
component_colors = {"Original": IMPRINT[0], "Trend": IMPRINT[1], "Seasonal": IMPRINT[2], "Residual": IMPRINT[3]}

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.5),
    axis_title=element_text(color=INK, size=16),
    axis_text=element_text(color=INK_SOFT, size=14),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=20, face="bold"),
)

# Plot 1: Original Series
p1 = (
    ggplot(df_original, aes(x="date", y="value"))
    + geom_line(color=component_colors["Original"], size=1.2)
    + labs(x="", y="Temperature (°C)", title="Original Series")
    + anyplot_theme
    + theme(axis_text_x=element_blank())
    + ggsize(1600, 200)
)

# Plot 2: Trend Component
p2 = (
    ggplot(df_trend.dropna(), aes(x="date", y="value"))
    + geom_line(color=component_colors["Trend"], size=1.2)
    + labs(x="", y="Temperature (°C)", title="Trend")
    + anyplot_theme
    + theme(axis_text_x=element_blank())
    + ggsize(1600, 200)
)

# Plot 3: Seasonal Component
p3 = (
    ggplot(df_seasonal, aes(x="date", y="value"))
    + geom_line(color=component_colors["Seasonal"], size=1.2)
    + labs(x="", y="Temperature (°C)", title="Seasonal")
    + anyplot_theme
    + theme(axis_text_x=element_blank())
    + ggsize(1600, 200)
)

# Plot 4: Residual Component
p4 = (
    ggplot(df_residual.dropna(), aes(x="date", y="value"))
    + geom_line(color=component_colors["Residual"], size=1.2)
    + labs(x="Date", y="Temperature (°C)", title="Residual")
    + anyplot_theme
    + theme(axis_text_x=element_text(angle=45))
    + ggsize(1600, 200)
)

# Create combined plot using gggrid
combined = gggrid([p1, p2, p3, p4], ncol=1)

# Add overall title
final_plot = (
    combined
    + ggsize(1600, 900)
    + ggtitle("timeseries-decomposition · letsplot · anyplot.ai")
    + theme(plot_title=element_text(color=INK, size=24, face="bold"))
)

# Save as PNG with scale for 4800x2700 resolution
ggsave(final_plot, f"plot-{THEME}.png", scale=3)

# Save HTML for interactive version
ggsave(final_plot, f"plot-{THEME}.html")

# Move files from lets-plot subdirectory to current directory if needed
lp_dir = "lets-plot-images"
if os.path.exists(lp_dir):
    for fname in [f"plot-{THEME}.png", f"plot-{THEME}.html"]:
        src = os.path.join(lp_dir, fname)
        if os.path.exists(src):
            shutil.move(src, fname)
    if not os.listdir(lp_dir):
        os.rmdir(lp_dir)
