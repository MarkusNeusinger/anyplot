""" pyplots.ai
candlestick-basic: Basic Candlestick Chart
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 90/100 | Updated: 2026-02-24
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter, Range1d
from bokeh.plotting import figure


# Data - Generate 30 trading days of OHLC data
np.random.seed(42)
n_days = 30
start_price = 150.0
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Generate realistic price movements with dip and recovery
returns = np.random.randn(n_days) * 0.018
returns[:10] -= 0.002
returns[10:20] -= 0.005
returns[20:] += 0.008
prices = start_price * np.cumprod(1 + returns)

# Generate OHLC data
open_prices = []
high_prices = []
low_prices = []
close_prices = []

for i, close in enumerate(prices):
    if i == 0:
        open_price = start_price
    else:
        open_price = close_prices[-1]

    daily_range = abs(np.random.randn()) * 0.012 * close
    high = max(open_price, close) + daily_range
    low = min(open_price, close) - daily_range

    open_prices.append(open_price)
    high_prices.append(high)
    low_prices.append(low)
    close_prices.append(close)

df = pd.DataFrame({"date": dates, "open": open_prices, "high": high_prices, "low": low_prices, "close": close_prices})
df["bullish"] = df["close"] >= df["open"]
df["date_str"] = df["date"].dt.strftime("%b %d, %Y")

# Separate sources for bullish and bearish candles
bullish_df = df[df["bullish"]].copy()
bearish_df = df[~df["bullish"]].copy()
source_bullish = ColumnDataSource(bullish_df)
source_bearish = ColumnDataSource(bearish_df)

# Colorblind-safe palette: Python Blue for bullish, burnt orange for bearish
color_bull = "#306998"
color_bear = "#E8590C"

# Create figure
p = figure(
    width=4800,
    height=2700,
    x_axis_type="datetime",
    title="ACME Corp Stock · candlestick-basic · bokeh · pyplots.ai",
    x_axis_label="Date",
    y_axis_label="Price ($)",
    tools="",
    toolbar_location=None,
)

# Tighten x-range to remove excess padding
x_pad = pd.Timedelta(days=1)
p.x_range = Range1d(start=dates[0] - x_pad, end=dates[-1] + x_pad)

# Candle width in milliseconds (75% of one business day)
candle_width = 0.75 * 24 * 60 * 60 * 1000

# Wicks - colored to match candle bodies
p.segment(x0="date", y0="high", x1="date", y1="low", source=source_bullish, color=color_bull, line_width=5)
p.segment(x0="date", y0="high", x1="date", y1="low", source=source_bearish, color=color_bear, line_width=5)

# Bullish candle bodies
bull_bars = p.vbar(
    x="date",
    top="close",
    bottom="open",
    width=candle_width,
    source=source_bullish,
    fill_color=color_bull,
    line_color=color_bull,
    line_width=2,
)

# Bearish candle bodies
bear_bars = p.vbar(
    x="date",
    top="open",
    bottom="close",
    width=candle_width,
    source=source_bearish,
    fill_color=color_bear,
    line_color=color_bear,
    line_width=2,
)

# Hover tooltips - distinctive Bokeh interactive feature
hover = HoverTool(
    renderers=[bull_bars, bear_bars],
    tooltips=[
        ("Date", "@date_str"),
        ("Open", "@open{$0.00}"),
        ("High", "@high{$0.00}"),
        ("Low", "@low{$0.00}"),
        ("Close", "@close{$0.00}"),
    ],
    mode="vline",
)
p.add_tools(hover)

# Text sizing for 4800x2700
p.title.text_font_size = "36pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Y-axis dollar formatting
p.yaxis.formatter = NumeralTickFormatter(format="$0")

# Grid - subtle y-axis only
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_width = 1

# Axis styling - softened for minimalist look
p.outline_line_color = None
p.xaxis.axis_line_width = 1
p.yaxis.axis_line_width = 1
p.xaxis.axis_line_alpha = 0.5
p.yaxis.axis_line_alpha = 0.5

# Remove tick marks (keep labels)
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML (interactive with hover tooltips)
save(p, filename="plot.html", title="candlestick-basic · bokeh · pyplots.ai")
