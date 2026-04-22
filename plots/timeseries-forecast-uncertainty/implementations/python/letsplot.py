""" pyplots.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 100/100 | Created: 2026-01-07
"""
# ruff: noqa: F405

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Data - Monthly product demand with 36 months history + 12 month forecast
np.random.seed(42)

# Historical period (36 months)
dates_hist = pd.date_range("2023-01-01", periods=36, freq="MS")
# Trend + seasonality + noise
trend = np.linspace(100, 150, 36)
seasonality = 15 * np.sin(np.linspace(0, 6 * np.pi, 36))
noise = np.random.normal(0, 5, 36)
actual = trend + seasonality + noise

# Forecast period (12 months)
dates_forecast = pd.date_range("2026-01-01", periods=12, freq="MS")
trend_fc = np.linspace(150, 170, 12)
seasonality_fc = 15 * np.sin(np.linspace(6 * np.pi, 8 * np.pi, 12))
forecast = trend_fc + seasonality_fc

# Uncertainty grows with forecast horizon
uncertainty_80 = np.linspace(8, 25, 12)
uncertainty_95 = np.linspace(12, 40, 12)

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

# Plot
plot = (
    ggplot()
    # 95% confidence band (lighter)
    + geom_ribbon(aes(x="date", ymin="lower_95", ymax="upper_95"), data=df_fc, fill="#FFD43B", alpha=0.3)
    # 80% confidence band (darker)
    + geom_ribbon(aes(x="date", ymin="lower_80", ymax="upper_80"), data=df_fc, fill="#FFD43B", alpha=0.5)
    # Historical and Forecast lines with legend
    + geom_line(aes(x="date", y="value", color="series"), data=df_lines, size=1.5)
    # Vertical line at forecast start
    + geom_vline(xintercept=forecast_start.timestamp() * 1000, color="#666666", size=1, linetype="dotted")
    # Manual color scale for series legend
    + scale_color_manual(values={"Historical": "#306998", "Forecast": "#DC2626"}, name="Series")
    # Labels
    + labs(
        x="Date",
        y="Product Demand (Units)",
        title="timeseries-forecast-uncertainty · letsplot · pyplots.ai",
        caption="Shaded bands: 80% CI (darker) and 95% CI (lighter)",
    )
    # Theme
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        plot_caption=element_text(size=14),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save PNG and HTML
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
