""" anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-16
"""
# ruff: noqa: F405

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette for categorical data
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data - Stock price with 36 months history + 12 month forecast
np.random.seed(42)

# Historical period (36 months)
dates_hist = pd.date_range("2023-01-01", periods=36, freq="MS")
# Trend + volatility + noise
trend = np.linspace(120, 185, 36)
volatility = 8 * np.sin(np.linspace(0, 4 * np.pi, 36))
noise = np.random.normal(0, 6, 36)
actual = trend + volatility + noise

# Forecast period (12 months)
dates_forecast = pd.date_range("2026-01-01", periods=12, freq="MS")
trend_fc = np.linspace(185, 210, 12)
volatility_fc = 8 * np.sin(np.linspace(4 * np.pi, 5 * np.pi, 12))
forecast = trend_fc + volatility_fc

# Uncertainty grows with forecast horizon (realistic for financial predictions)
uncertainty_80 = np.linspace(12, 35, 12)
uncertainty_95 = np.linspace(18, 55, 12)

# Build DataFrames
df_hist = pd.DataFrame({"date": dates_hist, "value": actual, "series": "Historical"})

df_fc = pd.DataFrame(
    {
        "date": dates_forecast,
        "value": forecast,
        "lower_80": forecast - uncertainty_80,
        "upper_80": forecast + uncertainty_80,
        "lower_95": forecast - uncertainty_95,
        "upper_95": forecast + uncertainty_95,
        "series": "Forecast",
    }
)

# Forecast start date for vertical line
forecast_start = dates_forecast[0]

# Combine line data for legend
df_lines = pd.concat([df_hist[["date", "value", "series"]], df_fc[["date", "value", "series"]]], ignore_index=True)

# Theme-adaptive theme
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_GRID, size=0.3),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
    plot_caption=element_text(color=INK_SOFT, size=14),
    legend_position="right",
)

# Plot
plot = (
    ggplot()
    # 95% confidence band (lighter, using position 5 - orange)
    + geom_ribbon(aes(x="date", ymin="lower_95", ymax="upper_95"), data=df_fc, fill=OKABE_ITO[4], alpha=0.2)
    # 80% confidence band (darker, using position 5 - orange)
    + geom_ribbon(aes(x="date", ymin="lower_80", ymax="upper_80"), data=df_fc, fill=OKABE_ITO[4], alpha=0.35)
    # Historical and Forecast lines with legend
    + geom_line(aes(x="date", y="value", color="series"), data=df_lines, size=1.5)
    # Vertical line at forecast start
    + geom_vline(xintercept=forecast_start.timestamp() * 1000, color=INK_SOFT, size=0.8, linetype="dotted")
    # Manual color scale: historical using brand green, forecast using orange
    + scale_color_manual(values={"Historical": OKABE_ITO[0], "Forecast": OKABE_ITO[4]}, name="Series")
    # Labels
    + labs(
        x="Date",
        y="Stock Price ($)",
        title="timeseries-forecast-uncertainty · letsplot · anyplot.ai",
        caption="Shaded bands: 80% confidence interval (darker) and 95% CI (lighter)",
    )
    # Base size scaled 3x on export = 4800 × 2700 px
    + ggsize(1600, 900)
    # Apply custom theme
    + anyplot_theme
)

# Save PNG and HTML with theme suffix
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
