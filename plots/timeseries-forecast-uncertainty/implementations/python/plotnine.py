""" anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-19
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_ribbon,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette
OKABE_ITO = {"Historical": "#009E73", "Forecast": "#D55E00"}

# Data - Monthly electricity demand with forecast
np.random.seed(42)

# Historical period: 36 months
n_historical = 36
dates_historical = pd.date_range("2022-01-01", periods=n_historical, freq="MS")

# Base trend with seasonality
trend = np.linspace(100, 130, n_historical)
seasonality = 15 * np.sin(2 * np.pi * np.arange(n_historical) / 12)
noise = np.random.normal(0, 5, n_historical)
actual_values = trend + seasonality + noise

# Forecast period: 12 months
n_forecast = 12
dates_forecast = pd.date_range(dates_historical[-1] + pd.DateOffset(months=1), periods=n_forecast, freq="MS")

# Forecast with expanding uncertainty
forecast_trend = np.linspace(actual_values[-1], 145, n_forecast)
forecast_seasonality = 15 * np.sin(2 * np.pi * (np.arange(n_forecast) + n_historical) / 12)
forecast_values = forecast_trend + forecast_seasonality

# Confidence intervals widen over time
time_factor = np.sqrt(np.arange(1, n_forecast + 1))
ci_80 = 5 * time_factor
ci_95 = 10 * time_factor

# Build dataframe for historical data
df_historical = pd.DataFrame({"date": dates_historical, "value": actual_values, "series": "Historical"})

# Build dataframe for forecast
df_forecast = pd.DataFrame(
    {
        "date": dates_forecast,
        "value": forecast_values,
        "lower_80": forecast_values - ci_80,
        "upper_80": forecast_values + ci_80,
        "lower_95": forecast_values - ci_95,
        "upper_95": forecast_values + ci_95,
        "series": "Forecast",
    }
)

# Forecast start date and annotation anchor
forecast_start = dates_forecast[0]
annotation_y = float(df_forecast["upper_95"].max()) + 5

# Plot
plot = (
    ggplot()
    # 95% confidence band (lighter, outer)
    + geom_ribbon(
        data=df_forecast,
        mapping=aes(x="date", ymin="lower_95", ymax="upper_95"),
        fill=OKABE_ITO["Forecast"],
        alpha=0.15,
    )
    # 80% confidence band (darker, inner)
    + geom_ribbon(
        data=df_forecast,
        mapping=aes(x="date", ymin="lower_80", ymax="upper_80"),
        fill=OKABE_ITO["Forecast"],
        alpha=0.30,
    )
    # Vertical line at forecast start
    + geom_vline(xintercept=forecast_start, linetype="dashed", color=INK_SOFT, size=0.8)
    # Forecast period label positioned above the vline
    + annotate("text", x=forecast_start, y=annotation_y, label="Forecast period", color=INK_MUTED, size=13, ha="center")
    # Historical line
    + geom_line(data=df_historical, mapping=aes(x="date", y="value", color="series"), size=1.5)
    # Forecast line
    + geom_line(data=df_forecast, mapping=aes(x="date", y="value", color="series"), size=1.5, linetype="dashed")
    # Color mapping with Okabe-Ito
    + scale_color_manual(values=OKABE_ITO, name="")
    # Labels
    + labs(
        x="Date",
        y="Electricity Demand (GWh)",
        title="timeseries-forecast-uncertainty · python · plotnine · anyplot.ai",
        subtitle="Shaded bands show 80% and 95% confidence intervals; uncertainty widens with forecast horizon",
    )
    # Date axis formatting
    + scale_x_datetime(date_breaks="6 months", date_labels="%b %Y")
    # Theme
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.1),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_text_x=element_text(angle=45, ha="right"),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, color=INK, weight="medium"),
        plot_subtitle=element_text(size=14, color=INK_MUTED),
        legend_position="top",
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
