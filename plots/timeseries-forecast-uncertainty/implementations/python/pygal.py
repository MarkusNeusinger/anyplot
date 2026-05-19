"""anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: pygal | Python 3.13
Quality: 92/100 | Created: 2026-05-16
"""

import os
import sys


sys.path[:] = [p for p in sys.path if p not in ("", ".", os.path.dirname(__file__))]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND = "#009E73"  # Okabe-Ito position 1
FORECAST_COLOR = "#D55E00"  # Okabe-Ito position 2

# Data
np.random.seed(42)
months = 42  # 36 historical + 6 forecast
dates = pd.date_range("2022-01-01", periods=months, freq="MS")
split_idx = 36  # Historical/forecast boundary

t = np.arange(split_idx)
base = 1000 + 50 * t + 100 * np.sin(2 * np.pi * t / 12)
noise = np.random.normal(0, 30, split_idx)
actual = base + noise

t_forecast = np.arange(split_idx, months)
forecast_base = actual[-1] + 30 * (t_forecast - split_idx)
forecast_values = forecast_base + 50 * np.sin(2 * np.pi * t_forecast / 12)

upper_95 = forecast_values + 150
lower_95 = forecast_values - 150
upper_80 = forecast_values + 100
lower_80 = forecast_values - 100

x_labels = [d.strftime("%b %y") for d in dates]
sparse_labels = [x_labels[i] if i % 6 == 0 else "" for i in range(len(x_labels))]

# Style — pygal's fill-opacity is a global Style attribute, not per-series.
# Colors are mapped to series order: hist, forecast, u95, l95-cover, u80, boundary.
# PAGE_BG at position 4 creates a partial "cover" below the 95% lower bound.
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND, FORECAST_COLOR, FORECAST_COLOR, PAGE_BG, FORECAST_COLOR, INK_MUTED),
    opacity=".6",
    title_font_size=18,
    label_font_size=14,
    major_label_font_size=12,
    legend_font_size=12,
    value_font_size=10,
    stroke_width=2.5,
)

# Chart
chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    show_x_guides=False,
    show_y_guides=True,
    show_legend=True,
    legend_at_bottom=False,
    dots_size=3,
    print_values=False,
    allow_interruptions=True,
)

chart.title = "timeseries-forecast-uncertainty · python · pygal · anyplot.ai"
chart.x_title = "Month"
chart.y_title = "Sales ($)"
chart.x_labels = sparse_labels

# Historical data — solid green line
chart.add("Historical (observed)", list(actual[:split_idx]), stroke_dasharray=(0,), color=BRAND, fill=False)

# Forecast — dashed orange line
chart.add(
    "Forecast (projected)",
    [None] * split_idx + list(forecast_values),
    stroke_dasharray=(5, 5),
    color=FORECAST_COLOR,
    fill=False,
)

# 95% CI outer band (fills from upper_95 down to chart floor — lighter fill from global opacity)
chart.add(
    "95% confidence interval",
    [None] * split_idx + list(upper_95),
    show_legend=True,
    stroke_dasharray=(0,),
    color=FORECAST_COLOR,
    fill=True,
)

# Partial PAGE_BG cover below lower_95 dampens the fill in the lower forecast region
chart.add(None, [None] * split_idx + list(lower_95), show_legend=False, stroke_dasharray=(0,), color=PAGE_BG, fill=True)

# 80% CI inner band (stacks on top of 95% fill — darker combined opacity)
chart.add(
    "80% confidence interval",
    [None] * split_idx + list(upper_80),
    show_legend=True,
    stroke_dasharray=(0,),
    color=FORECAST_COLOR,
    fill=True,
)

# Forecast boundary marker — explicit dot at history/forecast transition
boundary_series = [None] * months
boundary_series[split_idx] = forecast_values[0]
chart.add("Forecast start", boundary_series, color=INK_MUTED, fill=False, show_legend=True)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
