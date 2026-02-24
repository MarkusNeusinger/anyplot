"""pyplots.ai
candlestick-basic: Basic Candlestick Chart
Library: pygal 3.1.0 | Python 3.14.3
"""

import re
from datetime import datetime, timedelta

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# --- Data: 30 trading days of OHLC stock prices ---
np.random.seed(42)
n_days = 30

start_date = datetime(2024, 1, 2)
dates = []
cur = start_date
for _ in range(n_days):
    while cur.weekday() >= 5:
        cur += timedelta(days=1)
    dates.append(cur)
    cur += timedelta(days=1)

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
closes = [d["close"] for d in ohlc_data]
ma_points = [(i + 1, float(np.mean(closes[i - 4 : i + 1]))) for i in range(4, n_days)]

# Price extremes for storytelling markers
peak = max(ohlc_data, key=lambda d: d["high"])
trough = min(ohlc_data, key=lambda d: d["low"])

# --- Group candlestick segments by direction (None = line break) ---
bull_wicks, bear_wicks = [], []
bull_bodies, bear_bodies = [], []

for candle in ohlc_data:
    x = candle["day"]
    wick = [(x, candle["low"]), (x, candle["high"]), None]
    body = [(x, candle["open"]), (x, candle["close"]), None]
    if candle["close"] >= candle["open"]:
        bull_wicks.extend(wick)
        bull_bodies.extend(body)
    else:
        bear_wicks.extend(wick)
        bear_bodies.extend(body)

# --- Style: fully colorblind-safe palette ---
BULL, BEAR = "#2271B3", "#D66B27"
PEAK_CLR, LOW_CLR = "#7B4FA0", "#2A7B7B"  # Purple & teal (colorblind-safe)
MA_CLR = "#555555"
date_map = {i + 1: dates[i] for i in range(n_days)}

custom_style = Style(
    background="white",
    plot_background="#f4f4f0",
    foreground="#2a2a2a",
    foreground_strong="#1a1a1a",
    foreground_subtle="#dedede",
    colors=(BULL, BEAR, MA_CLR, BULL, BEAR, PEAK_CLR, LOW_CLR),
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=44,
    value_font_size=34,
)

# --- Chart configuration ---
WICK_W, BODY_W, MA_W = 20, 76, 6

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
    allow_interruptions=True,
    range=(min(d["low"] for d in ohlc_data) - 2, max(d["high"] for d in ohlc_data) + 3),
    xrange=(0, n_days + 1),
    legend_box_size=30,
    margin=40,
    spacing=25,
    tooltip_border_radius=8,
    truncate_legend=-1,
    value_formatter=lambda x: f"${x:.2f}",
)

chart.x_labels = [1, 5, 10, 15, 20, 25, 30]
chart.x_value_formatter = lambda x: date_map[int(round(x))].strftime("%b %d") if int(round(x)) in date_map else ""

# Series 0-1: Wicks (background, hidden from legend)
chart.add(None, bull_wicks, stroke=True, show_dots=False, stroke_style={"width": WICK_W, "linecap": "butt"})
chart.add(None, bear_wicks, stroke=True, show_dots=False, stroke_style={"width": WICK_W, "linecap": "butt"})

# Series 2: Moving average trend line
chart.add("5-Day MA", ma_points, stroke=True, show_dots=False, stroke_style={"width": MA_W, "linecap": "round"})

# Series 3-4: Candlestick bodies (foreground)
chart.add("Bullish (Up)", bull_bodies, stroke=True, show_dots=False, stroke_style={"width": BODY_W, "linecap": "butt"})
chart.add(
    "Bearish (Down)", bear_bodies, stroke=True, show_dots=False, stroke_style={"width": BODY_W, "linecap": "butt"}
)

# Series 5-6: Price extreme markers (colorblind-safe purple & teal)
chart.add(f"Peak ${peak['high']:.2f}", [(peak["day"], peak["high"])], stroke=False, show_dots=True, dots_size=16)
chart.add(f"Low ${trough['low']:.2f}", [(trough["day"], trough["low"])], stroke=False, show_dots=True, dots_size=16)

# --- Render: inline stroke styles for cairosvg compatibility ---
# cairosvg ignores CSS class-based stroke properties; inline them on every path per series
svg = chart.render(is_unicode=True)
series_strokes = {
    0: (WICK_W, "butt"),
    1: (WICK_W, "butt"),
    2: (MA_W, "round"),
    3: (BODY_W, "butt"),
    4: (BODY_W, "butt"),
}
for sid, (width, cap) in series_strokes.items():
    style_attr = f' style="stroke-width:{width};stroke-linecap:{cap}"'
    svg = re.sub(
        rf'(class="series serie-{sid} color-{sid}"[^>]*>.*?</g>)',
        lambda m, s=style_attr: m.group(0).replace('class="line reactive nofill"', 'class="line reactive nofill"' + s),
        svg,
        count=1,
        flags=re.DOTALL,
    )

cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to="plot.png")
with open("plot.html", "w") as f:
    f.write(chart.render(is_unicode=True))
