""" anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: pygal 3.1.0 | Python 3.13.13
Quality: 66/100 | Updated: 2026-05-19
"""

import os
import sys


# noqa: E402 - sys.path must be modified before imports to avoid module shadowing
sys.path[:] = [p for p in sys.path if p not in ("", ".", os.path.dirname(__file__))]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND = "#009E73"  # Okabe-Ito position 1
FORECAST_COLOR = "#D55E00"  # Okabe-Ito position 2

# Data
np.random.seed(42)
months = 42  # 36 historical + 6 forecast
dates = pd.date_range("2022-01-01", periods=months, freq="MS")
split_idx = 36  # Historical/forecast boundary

# Generate historical data with trend and seasonality
t = np.arange(split_idx)
base = 1000 + 50 * t + 100 * np.sin(2 * np.pi * t / 12)
noise = np.random.normal(0, 30, split_idx)
actual = base + noise

# Generate forecast with uncertainty
t_forecast = np.arange(split_idx, months)
forecast_base = actual[-1] + 30 * (t_forecast - split_idx)
forecast_values = forecast_base + 50 * np.sin(2 * np.pi * t_forecast / 12)

# Confidence intervals (wider for 95% than 80%)
upper_95 = forecast_values + 150
lower_95 = forecast_values - 150
upper_80 = forecast_values + 100
lower_80 = forecast_values - 100

# Prepare data for chart
x_labels = [d.strftime("%b %y") for d in dates]

# Create pygal style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND, FORECAST_COLOR),
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Create chart — show_x_guides=True draws a vertical line at x_labels_major positions
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    show_x_guides=True,
    show_y_guides=True,
    show_legend=True,
    legend_at_bottom=False,
    dots_size=3,
    print_values=False,
    print_values_position="top",
)

chart.title = "timeseries-forecast-uncertainty · python · pygal · anyplot.ai"
chart.x_title = "Month"
chart.y_title = "Sales ($)"

# Sparse x-axis labels: show every 6 months for readability
sparse_labels = [x_labels[i] if i % 6 == 0 else "" for i in range(len(x_labels))]
chart.x_labels = sparse_labels
# Draw the vertical forecast boundary guide only at the split month
chart.x_labels_major = ["Jan 25"]

# Prepare data series
historical_data = list(actual[:split_idx])
forecast_data = list(forecast_values)
upper_95_band = list(upper_95)
lower_95_band = list(lower_95)
upper_80_band = list(upper_80)
lower_80_band = list(lower_80)

# Add historical data - solid line emphasizing observed values
chart.add("Historical (observed)", historical_data, stroke_dasharray=(0,), color=BRAND, fill=False)

# Add forecast data - dashed line for distinct visual separation
chart.add(
    "Forecast (projected)",
    [None] * split_idx + forecast_data,
    stroke_dasharray=(5, 5),
    color=FORECAST_COLOR,
    fill=False,
)

# Add 95% confidence interval (outer band, lighter)
chart.add(
    "95% confidence interval",
    [None] * split_idx + upper_95_band,
    show_legend=True,
    stroke_dasharray=(0,),
    color=FORECAST_COLOR,
    opacity=0.15,
    fill=True,
)
chart.add(
    None,
    [None] * split_idx + lower_95_band,
    show_legend=False,
    stroke_dasharray=(0,),
    color=FORECAST_COLOR,
    opacity=0.15,
    fill=True,
)

# Add 80% confidence interval (inner band, more opaque)
chart.add(
    "80% confidence interval",
    [None] * split_idx + upper_80_band,
    show_legend=True,
    stroke_dasharray=(0,),
    color=FORECAST_COLOR,
    opacity=0.3,
    fill=True,
)
chart.add(
    None,
    [None] * split_idx + lower_80_band,
    show_legend=False,
    stroke_dasharray=(0,),
    color=FORECAST_COLOR,
    opacity=0.3,
    fill=True,
)

# Render outputs
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
