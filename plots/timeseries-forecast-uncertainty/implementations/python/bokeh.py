""" pyplots.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 97/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Label, Legend, NumeralTickFormatter, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Monthly product sales with forecast
np.random.seed(42)

# Historical data: 36 months (3 years)
n_historical = 36
dates_hist = pd.date_range("2022-01-01", periods=n_historical, freq="MS")
trend = np.linspace(80, 120, n_historical)
seasonal = 15 * np.sin(np.linspace(0, 6 * np.pi, n_historical))
noise = np.random.normal(0, 5, n_historical)
actual = trend + seasonal + noise

# Forecast data: 12 months
n_forecast = 12
dates_forecast = pd.date_range(dates_hist[-1] + pd.DateOffset(months=1), periods=n_forecast, freq="MS")
trend_forecast = np.linspace(120, 135, n_forecast)
seasonal_forecast = 15 * np.sin(np.linspace(6 * np.pi, 8 * np.pi, n_forecast))
forecast = trend_forecast + seasonal_forecast

# Uncertainty grows over time
uncertainty_80 = np.linspace(5, 15, n_forecast)
uncertainty_95 = np.linspace(8, 25, n_forecast)

lower_80 = forecast - uncertainty_80
upper_80 = forecast + uncertainty_80
lower_95 = forecast - uncertainty_95
upper_95 = forecast + uncertainty_95

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="timeseries-forecast-uncertainty · bokeh · pyplots.ai",
    x_axis_label="Date",
    y_axis_label="Sales (thousands)",
    x_axis_type="datetime",
)

# Style title and axes - larger for 4800x2700 canvas
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# 95% confidence band (lighter, drawn first)
source_95 = ColumnDataSource(
    data={"x": np.concatenate([dates_forecast, dates_forecast[::-1]]), "y": np.concatenate([upper_95, lower_95[::-1]])}
)
band_95 = p.patch(x="x", y="y", source=source_95, fill_color="#FFD43B", fill_alpha=0.25, line_color=None)

# 80% confidence band (darker, drawn on top)
source_80 = ColumnDataSource(
    data={"x": np.concatenate([dates_forecast, dates_forecast[::-1]]), "y": np.concatenate([upper_80, lower_80[::-1]])}
)
band_80 = p.patch(x="x", y="y", source=source_80, fill_color="#FFD43B", fill_alpha=0.5, line_color=None)

# Historical data line
source_hist = ColumnDataSource(data={"x": dates_hist, "y": actual})
hist_line = p.line(x="x", y="y", source=source_hist, line_color="#306998", line_width=5)

# Forecast line
source_forecast = ColumnDataSource(data={"x": dates_forecast, "y": forecast})
forecast_line = p.line(x="x", y="y", source=source_forecast, line_color="#E67E22", line_width=5, line_dash=[15, 8])

# Connection point - last historical to first forecast
source_connect = ColumnDataSource(data={"x": [dates_hist[-1], dates_forecast[0]], "y": [actual[-1], forecast[0]]})
p.line(x="x", y="y", source=source_connect, line_color="#E67E22", line_width=5, line_dash=[15, 8])

# Vertical line at forecast start
forecast_start = Span(
    location=dates_hist[-1], dimension="height", line_color="#555555", line_width=4, line_dash="dashed"
)
p.add_layout(forecast_start)

# Add text annotation for forecast start
forecast_label = Label(
    x=dates_hist[-1], y=165, text="Forecast Start", text_font_size="20pt", text_align="center", text_color="#555555"
)
p.add_layout(forecast_label)

# Legend
legend = Legend(
    items=[
        ("Historical Data", [hist_line]),
        ("Forecast", [forecast_line]),
        ("80% Confidence Interval", [band_80]),
        ("95% Confidence Interval", [band_95]),
    ],
    location="top_left",
)

legend.label_text_font_size = "24pt"
legend.background_fill_alpha = 0.9
legend.border_line_color = "#CCCCCC"
legend.border_line_width = 2
legend.padding = 15
legend.spacing = 10
legend.glyph_width = 40
legend.glyph_height = 25
p.add_layout(legend)

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Format y-axis
p.yaxis.formatter = NumeralTickFormatter(format="0")

# Axis line styling
p.axis.axis_line_width = 2
p.axis.major_tick_line_width = 2
p.axis.minor_tick_line_width = 1

# Remove toolbar for cleaner export
p.toolbar_location = None

# Add some padding to axis ranges
p.y_range.start = 55
p.y_range.end = 175

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="timeseries-forecast-uncertainty")
