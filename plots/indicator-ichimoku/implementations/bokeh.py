"""pyplots.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-12
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, NumeralTickFormatter, Range1d
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Generate 200 trading days of OHLC data with Ichimoku components
np.random.seed(42)
n_days = 200
start_price = 180.0
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Generate realistic price movements with trending phases
returns = np.random.randn(n_days) * 0.014
returns[:50] += 0.002
returns[50:100] -= 0.003
returns[100:150] += 0.004
returns[150:] -= 0.001
prices = start_price * np.cumprod(1 + returns)

# Generate OHLC from close prices
open_prices = np.empty(n_days)
high_prices = np.empty(n_days)
low_prices = np.empty(n_days)
close_prices = prices.copy()

open_prices[0] = start_price
for i in range(1, n_days):
    open_prices[i] = close_prices[i - 1]

for i in range(n_days):
    daily_range = abs(np.random.randn()) * 0.01 * close_prices[i]
    high_prices[i] = max(open_prices[i], close_prices[i]) + daily_range
    low_prices[i] = min(open_prices[i], close_prices[i]) - daily_range


# Compute Ichimoku components using pandas rolling on a DataFrame
ohlc_df = pd.DataFrame({"high": high_prices, "low": low_prices, "close": close_prices})

tenkan_sen = ((ohlc_df["high"].rolling(9).max() + ohlc_df["low"].rolling(9).min()) / 2).values
kijun_sen = ((ohlc_df["high"].rolling(26).max() + ohlc_df["low"].rolling(26).min()) / 2).values

# Senkou Span A and B: shifted 26 periods ahead
senkou_a_unshifted = (tenkan_sen + kijun_sen) / 2
senkou_b_unshifted = ((ohlc_df["high"].rolling(52).max() + ohlc_df["low"].rolling(52).min()) / 2).values

# Extend dates 26 periods into the future for senkou spans
future_dates = pd.date_range(start=dates[-1] + pd.tseries.offsets.BDay(1), periods=26, freq="B")
all_dates = dates.union(future_dates)

senkou_span_a = np.full(n_days + 26, np.nan)
senkou_span_b = np.full(n_days + 26, np.nan)
senkou_span_a[26 : n_days + 26] = senkou_a_unshifted
senkou_span_b[26 : n_days + 26] = senkou_b_unshifted

# Chikou Span: close shifted 26 periods into the past
chikou_span = np.full(n_days, np.nan)
chikou_span[: n_days - 26] = close_prices[26:]

# Build DataFrames
df = pd.DataFrame(
    {
        "date": dates,
        "open": open_prices,
        "high": high_prices,
        "low": low_prices,
        "close": close_prices,
        "tenkan": tenkan_sen,
        "kijun": kijun_sen,
        "chikou": chikou_span,
    }
)
df["bullish"] = df["close"] >= df["open"]
df["date_str"] = df["date"].dt.strftime("%b %d, %Y")

# Cloud DataFrame (extended with future dates)
cloud_df = pd.DataFrame({"date": all_dates, "span_a": senkou_span_a, "span_b": senkou_span_b})
cloud_df = cloud_df.dropna().reset_index(drop=True)

# Split cloud into bullish (A >= B) and bearish (B > A) segments for coloring
cloud_df["bullish_cloud"] = cloud_df["span_a"] >= cloud_df["span_b"]

# Candlestick sources
bullish_df = df[df["bullish"]].copy()
bearish_df = df[~df["bullish"]].copy()
source_bull = ColumnDataSource(bullish_df)
source_bear = ColumnDataSource(bearish_df)

# Colors
color_bull_candle = "#26A69A"
color_bear_candle = "#EF5350"
color_tenkan = "#2962FF"
color_kijun = "#B71C1C"
color_chikou = "#7B1FA2"
color_cloud_bull = "#26A69A"
color_cloud_bear = "#EF5350"

# Create figure
p = figure(
    width=4800,
    height=2700,
    x_axis_type="datetime",
    title="indicator-ichimoku · bokeh · pyplots.ai",
    x_axis_label="Date",
    y_axis_label="Price ($)",
    tools="",
    toolbar_location=None,
)

# X-range with padding for future cloud projection
x_pad = pd.Timedelta(days=3)
p.x_range = Range1d(start=dates[51] - x_pad, end=all_dates[-1] + x_pad)

# Plot cloud (Kumo) - draw filled area between Span A and Span B
# Use varea for each contiguous bullish/bearish segment
cloud_source = ColumnDataSource(cloud_df)

# Bullish cloud segments
bull_cloud = cloud_df[cloud_df["bullish_cloud"]].copy()
bear_cloud = cloud_df[~cloud_df["bullish_cloud"]].copy()

if len(bull_cloud) > 0:
    src_bull_cloud = ColumnDataSource(bull_cloud)
    r_cloud_bull = p.varea(
        x="date", y1="span_a", y2="span_b", source=src_bull_cloud, fill_color=color_cloud_bull, fill_alpha=0.25
    )

if len(bear_cloud) > 0:
    src_bear_cloud = ColumnDataSource(bear_cloud)
    r_cloud_bear = p.varea(
        x="date", y1="span_a", y2="span_b", source=src_bear_cloud, fill_color=color_cloud_bear, fill_alpha=0.25
    )

# Cloud boundary lines
span_a_source = ColumnDataSource(cloud_df[["date", "span_a"]].rename(columns={"span_a": "value"}))
span_b_source = ColumnDataSource(cloud_df[["date", "span_b"]].rename(columns={"span_b": "value"}))
p.line(x="date", y="value", source=span_a_source, line_color=color_cloud_bull, line_width=2, line_alpha=0.6)
p.line(x="date", y="value", source=span_b_source, line_color=color_cloud_bear, line_width=2, line_alpha=0.6)

# Candlestick wicks
candle_width = 0.6 * 24 * 60 * 60 * 1000

p.segment(x0="date", y0="high", x1="date", y1="low", source=source_bull, color=color_bull_candle, line_width=3)
p.segment(x0="date", y0="high", x1="date", y1="low", source=source_bear, color=color_bear_candle, line_width=3)

# Candlestick bodies
bull_bars = p.vbar(
    x="date",
    top="close",
    bottom="open",
    width=candle_width,
    source=source_bull,
    fill_color=color_bull_candle,
    line_color=color_bull_candle,
    line_width=2,
)
bear_bars = p.vbar(
    x="date",
    top="open",
    bottom="close",
    width=candle_width,
    source=source_bear,
    fill_color=color_bear_candle,
    line_color=color_bear_candle,
    line_width=2,
)

# Ichimoku lines
line_df = df.dropna(subset=["tenkan", "kijun"]).copy()
line_source = ColumnDataSource(line_df)

r_tenkan = p.line(x="date", y="tenkan", source=line_source, line_color=color_tenkan, line_width=3)
r_kijun = p.line(x="date", y="kijun", source=line_source, line_color=color_kijun, line_width=3)

# Chikou Span
chikou_df = df.dropna(subset=["chikou"]).copy()
chikou_source = ColumnDataSource(chikou_df)
r_chikou = p.line(x="date", y="chikou", source=chikou_source, line_color=color_chikou, line_width=2, line_dash="dashed")

# Legend
legend_items = [
    ("Tenkan-sen (9)", [r_tenkan]),
    ("Kijun-sen (26)", [r_kijun]),
    ("Chikou Span", [r_chikou]),
    ("Kumo (bullish)", [r_cloud_bull]),
    ("Kumo (bearish)", [r_cloud_bear]),
]
legend = Legend(items=legend_items, location="top_left")
legend.label_text_font_size = "22pt"
legend.glyph_height = 30
legend.glyph_width = 40
legend.spacing = 12
legend.padding = 15
legend.background_fill_alpha = 0.85
legend.background_fill_color = "#ffffff"
legend.border_line_color = "#dddddd"
p.add_layout(legend, "right")

# Hover tooltip
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

# Axis styling
p.outline_line_color = None
p.xaxis.axis_line_width = 1
p.yaxis.axis_line_width = 1
p.xaxis.axis_line_alpha = 0.5
p.yaxis.axis_line_alpha = 0.5

# Remove tick marks
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="indicator-ichimoku · bokeh · pyplots.ai")
