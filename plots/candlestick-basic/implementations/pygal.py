""" pyplots.ai
candlestick-basic: Basic Candlestick Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 83/100 | Updated: 2026-02-24
"""

import re
from datetime import datetime, timedelta

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data - Stock OHLC data for 30 trading days
np.random.seed(42)
n_days = 30

# Generate trading dates (skip weekends)
start_date = datetime(2024, 1, 2)
dates = []
cur = start_date
for _ in range(n_days):
    while cur.weekday() >= 5:
        cur += timedelta(days=1)
    dates.append(cur)
    cur += timedelta(days=1)

# Generate realistic OHLC data with trend and volatility
base_price = 150.0
returns = np.random.randn(n_days) * 2.5
price_series = base_price * np.cumprod(1 + returns / 100)

ohlc_data = []
for i, close in enumerate(price_series):
    volatility = np.abs(np.random.randn()) * 2 + 0.5
    intraday_range = close * volatility / 100
    open_price = base_price if i == 0 else ohlc_data[-1]["close"]
    high = max(open_price, close) + np.random.rand() * intraday_range
    low = min(open_price, close) - np.random.rand() * intraday_range
    ohlc_data.append({"day": i + 1, "open": open_price, "high": high, "low": low, "close": close})

# 5-day moving average for trend context
ma_period = 5
closes = [d["close"] for d in ohlc_data]
ma_points = [(i + 1, float(np.mean(closes[i - ma_period + 1 : i + 1]))) for i in range(ma_period - 1, n_days)]

# Price range with padding
y_min = min(d["low"] for d in ohlc_data) - 3
y_max = max(d["high"] for d in ohlc_data) + 3

# Colors - blue/orange colorblind-safe palette
bullish_color = "#2271B3"
bearish_color = "#D66B27"
ma_color = "#888888"

# Build color list: 30 wicks + 1 MA line + 30 bodies
colors_list = [bullish_color if d["close"] >= d["open"] else bearish_color for d in ohlc_data]
colors_list.append(ma_color)
colors_list.extend(bullish_color if d["close"] >= d["open"] else bearish_color for d in ohlc_data)

# Date lookup for x-axis formatting
date_map = {i + 1: dates[i] for i in range(n_days)}

# Refined style for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="#f8f8f8",
    foreground="#2a2a2a",
    foreground_strong="#2a2a2a",
    foreground_subtle="#dedede",
    colors=tuple(colors_list),
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=32,
)

# Chart with date-formatted x-axis
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="candlestick-basic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Date",
    y_title="Price ($)",
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    range=(y_min, y_max),
    xrange=(0, n_days + 1),
    show_legend=True,
    legend_at_bottom=False,
    legend_box_size=28,
    margin=50,
    spacing=30,
    tooltip_border_radius=8,
    value_formatter=lambda x: f"${x:.2f}",
)

# Date-formatted x-axis labels (every 5 trading days + last day)
chart.x_labels = [1, 5, 10, 15, 20, 25, 30]
chart.x_value_formatter = lambda x: date_map[int(round(x))].strftime("%b %d") if int(round(x)) in date_map else ""

# Stroke dimensions for 4800px canvas
wick_width = 20
body_width = 72

# Legend tracking
bullish_legend_done = False
bearish_legend_done = False

# Wicks (background layer)
for candle in ohlc_data:
    day = candle["day"]
    chart.add(
        None,
        [(day, candle["low"]), (day, candle["high"])],
        stroke=True,
        show_dots=False,
        stroke_style={"width": wick_width, "linecap": "butt"},
    )

# Moving average trend line (middle layer - behind bodies, above wicks)
chart.add("5-Day MA", ma_points, stroke=True, show_dots=False, stroke_style={"width": 6, "linecap": "round"})

# Bodies (foreground layer) with legend entries
for candle in ohlc_data:
    day = candle["day"]
    is_bullish = candle["close"] >= candle["open"]
    if is_bullish and not bullish_legend_done:
        label = "Bullish (Up)"
        bullish_legend_done = True
    elif not is_bullish and not bearish_legend_done:
        label = "Bearish (Down)"
        bearish_legend_done = True
    else:
        label = None
    chart.add(
        label,
        [(day, candle["open"]), (day, candle["close"])],
        stroke=True,
        show_dots=False,
        stroke_style={"width": body_width, "linecap": "butt"},
    )

# Inline stroke styles for cairosvg PNG compatibility
svg_content = chart.render(is_unicode=True)
css = re.search(r"<style[^>]*>(.*?)</style>", svg_content, re.DOTALL)
if css:
    for m in re.finditer(r"\.serie-(\d+)\{stroke-width:(\d+);stroke-linecap:(\w+)\}", css.group(1)):
        sid, sw, lc = m.groups()
        svg_content = re.sub(
            rf'(class="series serie-{sid} color-{sid}">[\s\S]*?'
            rf'class="line reactive nofill")',
            rf'\1 style="stroke-width:{sw};stroke-linecap:{lc}"',
            svg_content,
            count=1,
        )

# Save
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to="plot.png")
with open("plot.html", "w") as f:
    f.write(svg_content)
