""" pyplots.ai
candlestick-basic: Basic Candlestick Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: /100 | Updated: 2026-02-24
"""

import re

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data - Stock OHLC data for 30 trading days
np.random.seed(42)
n_days = 30

# Generate realistic OHLC data with trend and volatility
base_price = 150.0
returns = np.random.randn(n_days) * 2.5
price_series = base_price * np.cumprod(1 + returns / 100)

ohlc_data = []
for i, close in enumerate(price_series):
    volatility = np.abs(np.random.randn()) * 2 + 0.5
    intraday_range = close * volatility / 100

    if i == 0:
        open_price = base_price
    else:
        open_price = ohlc_data[-1]["close"]

    high = max(open_price, close) + np.random.rand() * intraday_range
    low = min(open_price, close) - np.random.rand() * intraday_range

    ohlc_data.append({"day": i + 1, "open": open_price, "high": high, "low": low, "close": close})

# Price range for chart
all_highs = [d["high"] for d in ohlc_data]
all_lows = [d["low"] for d in ohlc_data]
y_min = min(all_lows) - 2
y_max = max(all_highs) + 2

# Colors - blue/orange for colorblind safety
bullish_color = "#2271B3"
bearish_color = "#D66B27"

# Build color list: wicks (30 series) then bodies (30 series)
colors_list = []
for candle in ohlc_data:
    is_bullish = candle["close"] >= candle["open"]
    colors_list.append(bullish_color if is_bullish else bearish_color)
for candle in ohlc_data:
    is_bullish = candle["close"] >= candle["open"]
    colors_list.append(bullish_color if is_bullish else bearish_color)

# Style for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#e0e0e0",
    colors=tuple(colors_list),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
)

# Chart
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="candlestick-basic · pygal · pyplots.ai",
    x_title="Trading Day",
    y_title="Price ($)",
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    range=(y_min, y_max),
    xrange=(0, n_days + 1),
    show_legend=True,
    legend_at_bottom=False,
    legend_box_size=32,
    margin=60,
    spacing=40,
)

# Stroke dimensions for 4800px canvas
wick_width = 24
body_width = 80

# Track legend state
bullish_legend_done = False
bearish_legend_done = False

# Wicks first (rendered behind bodies in SVG layer order)
for candle in ohlc_data:
    day = candle["day"]
    chart.add(
        None,
        [(day, candle["low"]), (day, candle["high"])],
        stroke=True,
        show_dots=False,
        stroke_style={"width": wick_width, "linecap": "butt"},
    )

# Bodies on top with legend entries
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

# Render SVG and inline stroke-width on path elements for cairosvg PNG compatibility
svg_content = chart.render().decode("utf-8")

stroke_styles = {}
style_match = re.search(r"<style[^>]*>(.*?)</style>", svg_content, re.DOTALL)
if style_match:
    for m in re.finditer(r"\.series\.serie-(\d+)\{stroke-width:(\d+);stroke-linecap:(\w+)\}", style_match.group(1)):
        stroke_styles[m.group(1)] = (m.group(2), m.group(3))

for serie_id, (width, linecap) in stroke_styles.items():
    svg_content = re.sub(
        rf'(class="series serie-{serie_id} color-{serie_id}">'
        r'<path d="[^"]*" class="line reactive nofill")',
        rf'\1 style="stroke-width:{width};stroke-linecap:{linecap}"',
        svg_content,
    )

# Save
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to="plot.png")
with open("plot.html", "w") as f:
    f.write(svg_content)
