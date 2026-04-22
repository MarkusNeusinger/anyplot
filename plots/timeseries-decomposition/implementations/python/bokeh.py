""" pyplots.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png
from bokeh.layouts import column
from bokeh.models import Title
from bokeh.plotting import figure
from statsmodels.tsa.seasonal import seasonal_decompose


# Data - Monthly airline passengers (classic time series dataset)
np.random.seed(42)
date_range = pd.date_range(start="2018-01-01", periods=120, freq="MS")  # 10 years monthly

# Generate realistic airline passenger data with trend, seasonality, and noise
trend = np.linspace(100, 250, 120)  # Upward trend in thousands of passengers
seasonal_pattern = 30 * np.sin(2 * np.pi * np.arange(120) / 12)  # Annual seasonality
noise = np.random.normal(0, 10, 120)
passengers = trend + seasonal_pattern + noise

# Create DataFrame and perform decomposition
df = pd.DataFrame({"date": date_range, "passengers": passengers})
df.set_index("date", inplace=True)
decomposition = seasonal_decompose(df["passengers"], model="additive", period=12)

# Extract components
dates = df.index.to_list()
original = df["passengers"].values
trend_component = decomposition.trend.values
seasonal_component = decomposition.seasonal.values
residual_component = decomposition.resid.values

# Color scheme (Python Blue primary)
line_color = "#306998"

# Create subplots (4800 x 2700 total, divided into 4 panels)
panel_height = 620

# Panel 1: Original Series
p1 = figure(width=4800, height=panel_height, x_axis_type="datetime")
p1.line(dates, original, line_width=4, color=line_color)
p1.title.text = "Original Series"
p1.title.text_font_size = "26pt"
p1.yaxis.axis_label = "Passengers (thousands)"
p1.yaxis.axis_label_text_font_size = "22pt"
p1.xaxis.major_label_text_font_size = "18pt"
p1.yaxis.major_label_text_font_size = "18pt"
p1.xgrid.grid_line_alpha = 0.3
p1.ygrid.grid_line_alpha = 0.3
p1.xgrid.grid_line_dash = "dashed"
p1.ygrid.grid_line_dash = "dashed"
p1.outline_line_color = None
p1.xaxis.visible = False
p1.min_border_left = 120

# Panel 2: Trend Component
p2 = figure(width=4800, height=panel_height, x_axis_type="datetime", x_range=p1.x_range)
p2.line(dates, trend_component, line_width=4, color=line_color)
p2.title.text = "Trend Component"
p2.title.text_font_size = "26pt"
p2.yaxis.axis_label = "Trend"
p2.yaxis.axis_label_text_font_size = "22pt"
p2.xaxis.major_label_text_font_size = "18pt"
p2.yaxis.major_label_text_font_size = "18pt"
p2.xgrid.grid_line_alpha = 0.3
p2.ygrid.grid_line_alpha = 0.3
p2.xgrid.grid_line_dash = "dashed"
p2.ygrid.grid_line_dash = "dashed"
p2.outline_line_color = None
p2.xaxis.visible = False
p2.min_border_left = 120

# Panel 3: Seasonal Component
p3 = figure(width=4800, height=panel_height, x_axis_type="datetime", x_range=p1.x_range)
p3.line(dates, seasonal_component, line_width=4, color=line_color)
p3.title.text = "Seasonal Component"
p3.title.text_font_size = "26pt"
p3.yaxis.axis_label = "Seasonal"
p3.yaxis.axis_label_text_font_size = "22pt"
p3.xaxis.major_label_text_font_size = "18pt"
p3.yaxis.major_label_text_font_size = "18pt"
p3.xgrid.grid_line_alpha = 0.3
p3.ygrid.grid_line_alpha = 0.3
p3.xgrid.grid_line_dash = "dashed"
p3.ygrid.grid_line_dash = "dashed"
p3.outline_line_color = None
p3.xaxis.visible = False
p3.min_border_left = 120

# Panel 4: Residual Component
p4 = figure(width=4800, height=panel_height, x_axis_type="datetime", x_range=p1.x_range)
p4.line(dates, residual_component, line_width=4, color=line_color)
p4.title.text = "Residual Component"
p4.title.text_font_size = "26pt"
p4.yaxis.axis_label = "Residual"
p4.yaxis.axis_label_text_font_size = "22pt"
p4.xaxis.axis_label = "Date"
p4.xaxis.axis_label_text_font_size = "22pt"
p4.xaxis.major_label_text_font_size = "18pt"
p4.yaxis.major_label_text_font_size = "18pt"
p4.xgrid.grid_line_alpha = 0.3
p4.ygrid.grid_line_alpha = 0.3
p4.xgrid.grid_line_dash = "dashed"
p4.ygrid.grid_line_dash = "dashed"
p4.outline_line_color = None
p4.min_border_left = 120

# Add main title to top panel
p1.add_layout(
    Title(text="timeseries-decomposition · bokeh · pyplots.ai", text_font_size="32pt", align="center"), "above"
)

# Combine all panels into vertical layout
layout = column(p1, p2, p3, p4)

# Save
export_png(layout, filename="plot.png")
