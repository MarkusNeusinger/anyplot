"""anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-19
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
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
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
df_forecast = pd.DataFrame({"date": dates_forecast, "value": forecast_values, "series": "Forecast"})

# CI band dataframes with label column for legend mapping
df_ci_95 = pd.DataFrame(
    {"date": dates_forecast, "ymin": forecast_values - ci_95, "ymax": forecast_values + ci_95, "ci": "95% CI"}
)
df_ci_80 = pd.DataFrame(
    {"date": dates_forecast, "ymin": forecast_values - ci_80, "ymax": forecast_values + ci_80, "ci": "80% CI"}
)

# Forecast start date and annotation anchor
forecast_start = dates_forecast[0]
annotation_x = forecast_start + pd.DateOffset(months=1)
annotation_y = float(df_ci_95["ymax"].max()) + 5

# CI fill colors (same hue; alpha per-geom creates visual depth difference)
CI_COLORS = {"95% CI": OKABE_ITO["Forecast"], "80% CI": OKABE_ITO["Forecast"]}

# Plot
plot = (
    ggplot()
    # 95% confidence band (lighter, outer) — fill mapped for legend entry
    + geom_ribbon(data=df_ci_95, mapping=aes(x="date", ymin="ymin", ymax="ymax", fill="ci"), alpha=0.20)
    # 80% confidence band (darker, inner) — fill mapped for legend entry
    + geom_ribbon(data=df_ci_80, mapping=aes(x="date", ymin="ymin", ymax="ymax", fill="ci"), alpha=0.30)
    # Vertical line at forecast start
    + geom_vline(xintercept=forecast_start, linetype="dashed", color=INK_SOFT, size=0.8)
    # Forecast period label offset right so text clears the vline
    + annotate("text", x=annotation_x, y=annotation_y, label="Forecast period", color=INK_MUTED, size=9, ha="left")
    # Historical line
    + geom_line(data=df_historical, mapping=aes(x="date", y="value", color="series"), size=1.0)
    # Forecast line (dashed)
    + geom_line(data=df_forecast, mapping=aes(x="date", y="value", color="series"), size=1.0, linetype="dashed")
    # Color mapping for lines
    + scale_color_manual(values=OKABE_ITO)
    # Fill mapping for CI bands with legend entries
    + scale_fill_manual(values=CI_COLORS, name="CI bands")
    # Suppress "series" column header from color legend
    + guides(color=guide_legend(title=""))
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
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.1),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_text(angle=45, ha="right"),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=12, color=INK, weight="medium"),
        plot_subtitle=element_text(size=9, color=INK_MUTED),
        legend_position="top",
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
