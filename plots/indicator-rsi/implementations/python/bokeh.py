""" pyplots.ai
indicator-rsi: RSI Technical Indicator Chart
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import BoxAnnotation, ColumnDataSource, Legend, LegendItem, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Generate realistic stock price data and calculate RSI
np.random.seed(42)
n_days = 120

# Generate price data with realistic movements
dates = pd.date_range(start="2024-01-01", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.02, n_days)
returns[30:40] = np.random.normal(0.02, 0.01, 10)  # Strong uptrend (will push RSI high)
returns[60:75] = np.random.normal(-0.015, 0.01, 15)  # Downtrend (will push RSI low)
returns[95:105] = np.random.normal(0.018, 0.01, 10)  # Another uptrend
price = 100 * np.exp(np.cumsum(returns))

# Calculate RSI with 14-period lookback
period = 14
delta = np.diff(price)
gains = np.where(delta > 0, delta, 0)
losses = np.where(delta < 0, -delta, 0)

# Calculate initial average gain/loss
avg_gain = np.zeros(len(price))
avg_loss = np.zeros(len(price))
avg_gain[period] = np.mean(gains[:period])
avg_loss[period] = np.mean(losses[:period])

# Smoothed RSI calculation
for i in range(period + 1, len(price)):
    avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i - 1]) / period
    avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i - 1]) / period

rs = np.divide(avg_gain, avg_loss, out=np.zeros_like(avg_gain), where=avg_loss != 0)
rsi = 100 - (100 / (1 + rs))
rsi[:period] = np.nan  # RSI not valid for first 'period' values

# Prepare data
df = pd.DataFrame({"date": dates, "rsi": rsi})
df = df.dropna()
source = ColumnDataSource(df)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="indicator-rsi · bokeh · pyplots.ai",
    x_axis_label="Date",
    y_axis_label="RSI (14-Period)",
    x_axis_type="datetime",
    y_range=(0, 100),
)

# Styling
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Add shaded zones for overbought and oversold
overbought_zone = BoxAnnotation(bottom=70, top=100, fill_alpha=0.15, fill_color="#FF6B6B", level="underlay")
oversold_zone = BoxAnnotation(bottom=0, top=30, fill_alpha=0.15, fill_color="#4ECDC4", level="underlay")
p.add_layout(overbought_zone)
p.add_layout(oversold_zone)

# Add threshold lines
overbought_line = Span(location=70, dimension="width", line_color="#E74C3C", line_width=3, line_dash="dashed")
oversold_line = Span(location=30, dimension="width", line_color="#27AE60", line_width=3, line_dash="dashed")
centerline = Span(location=50, dimension="width", line_color="#95A5A6", line_width=2, line_dash="dotted")
p.add_layout(overbought_line)
p.add_layout(oversold_line)
p.add_layout(centerline)

# Plot RSI line
rsi_line = p.line(x="date", y="rsi", source=source, line_width=4, line_color="#306998", alpha=0.9)

# Add scatter points at extremes for emphasis
extreme_high = df[df["rsi"] >= 70].copy()
extreme_low = df[df["rsi"] <= 30].copy()

if not extreme_high.empty:
    source_high = ColumnDataSource(extreme_high)
    p.scatter(x="date", y="rsi", source=source_high, size=18, color="#E74C3C", alpha=0.8)

if not extreme_low.empty:
    source_low = ColumnDataSource(extreme_low)
    p.scatter(x="date", y="rsi", source=source_low, size=18, color="#27AE60", alpha=0.8)

# Create legend manually
legend_items = [LegendItem(label="RSI (14)", renderers=[rsi_line])]
legend = Legend(items=legend_items, location="top_right", label_text_font_size="18pt")
p.add_layout(legend)

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Background
p.background_fill_color = "#FAFAFA"

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="indicator-rsi · bokeh · pyplots.ai")
