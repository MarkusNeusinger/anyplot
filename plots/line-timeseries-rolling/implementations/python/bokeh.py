""" pyplots.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Simulated daily temperature readings over a year
np.random.seed(42)
n_days = 365
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")

# Create realistic temperature data with seasonal pattern and noise
day_of_year = np.arange(n_days)
seasonal_pattern = 15 * np.sin(2 * np.pi * (day_of_year - 80) / 365) + 20  # Peak in summer
noise = np.random.normal(0, 3, n_days)
temperature = seasonal_pattern + noise

# Calculate 30-day rolling average
rolling_window = 30
rolling_avg = pd.Series(temperature).rolling(window=rolling_window, center=True).mean()

# Create DataFrame
df = pd.DataFrame({"date": dates, "value": temperature, "rolling_avg": rolling_avg})

# Create ColumnDataSource for raw data
source_raw = ColumnDataSource(data={"date": df["date"], "value": df["value"]})

# Create ColumnDataSource for rolling average (exclude NaN values)
df_rolling = df.dropna(subset=["rolling_avg"])
source_rolling = ColumnDataSource(data={"date": df_rolling["date"], "rolling_avg": df_rolling["rolling_avg"]})

# Create figure - 4800 × 2700 px (16:9 landscape)
p = figure(
    width=4800,
    height=2700,
    title="line-timeseries-rolling · bokeh · pyplots.ai",
    x_axis_label="Date",
    y_axis_label="Temperature (°C)",
    x_axis_type="datetime",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Plot raw data - thin line with transparency
raw_line = p.line(
    x="date", y="value", source=source_raw, line_width=2, line_alpha=0.5, line_color="#306998", legend_label="Raw Data"
)

# Plot rolling average - prominent smooth line
rolling_line = p.line(
    x="date",
    y="rolling_avg",
    source=source_rolling,
    line_width=4,
    line_color="#FFD43B",
    legend_label=f"{rolling_window}-Day Rolling Average",
)

# Styling for large canvas
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling - subtle
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

# Legend styling
p.legend.label_text_font_size = "18pt"
p.legend.location = "top_left"
p.legend.background_fill_alpha = 0.8
p.legend.border_line_alpha = 0.3

# Background
p.background_fill_color = "#fafafa"

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactive version
output_file("plot.html")
save(p)
