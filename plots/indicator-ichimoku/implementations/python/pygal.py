""" pyplots.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 76/100 | Created: 2026-03-12
"""

import re
from datetime import datetime, timedelta

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data: 180 trading days of OHLC stock prices with Ichimoku components
np.random.seed(42)
n_days = 180

start_date = datetime(2024, 1, 2)
dates = []
cur = start_date
for _ in range(n_days):
    while cur.weekday() >= 5:
        cur += timedelta(days=1)
    dates.append(cur)
    cur += timedelta(days=1)

base_price = 175.0
returns = np.random.randn(n_days) * 1.8
price_series = base_price * np.cumprod(1 + returns / 100)

ohlc = []
for i, close in enumerate(price_series):
    volatility = np.abs(np.random.randn()) * 1.5 + 0.3
    intraday_range = close * volatility / 100
    open_price = base_price if i == 0 else ohlc[-1]["close"]
    high = max(open_price, close) + np.random.rand() * intraday_range
    low = min(open_price, close) - np.random.rand() * intraday_range
    ohlc.append({"open": open_price, "high": high, "low": low, "close": close})

highs = np.array([d["high"] for d in ohlc])
lows = np.array([d["low"] for d in ohlc])
closes = np.array([d["close"] for d in ohlc])

# Ichimoku calculations (9, 26, 52)
TENKAN_P, KIJUN_P, SENKOU_B_P, SHIFT = 9, 26, 52, 26

tenkan_sen = np.full(n_days, np.nan)
kijun_sen = np.full(n_days, np.nan)
senkou_a = np.full(n_days + SHIFT, np.nan)
senkou_b = np.full(n_days + SHIFT, np.nan)
chikou_span = np.full(n_days, np.nan)

for i in range(n_days):
    if i >= TENKAN_P - 1:
        tenkan_sen[i] = (highs[i - TENKAN_P + 1 : i + 1].max() + lows[i - TENKAN_P + 1 : i + 1].min()) / 2
    if i >= KIJUN_P - 1:
        kijun_sen[i] = (highs[i - KIJUN_P + 1 : i + 1].max() + lows[i - KIJUN_P + 1 : i + 1].min()) / 2
    if i >= KIJUN_P - 1:
        senkou_a[i + SHIFT] = (tenkan_sen[i] + kijun_sen[i]) / 2
    if i >= SENKOU_B_P - 1:
        senkou_b[i + SHIFT] = (highs[i - SENKOU_B_P + 1 : i + 1].max() + lows[i - SENKOU_B_P + 1 : i + 1].min()) / 2
    if i >= SHIFT:
        chikou_span[i - SHIFT] = closes[i]

# Display range: show days 60-180 (120 days) for clear Ichimoku signals
VIEW_START, VIEW_END = 60, n_days
total_x = VIEW_END - VIEW_START + SHIFT

# Colors — distinct palettes for candles vs Ichimoku components
# Candles: dark saturated tones for prominence against lighter cloud fills
BULL_CLR, BEAR_CLR = "#1B7A3D", "#B91C1C"
# Ichimoku lines: clearly different hues from candles
TENKAN_CLR, KIJUN_CLR = "#E6550D", "#306998"
SPAN_A_CLR, SPAN_B_CLR = "#66BB6A", "#EF5350"
CHIKOU_CLR = "#8E44AD"
# Cloud fills: muted green/red tints so candles stand out
CLOUD_BULL = "#A5D6A7"
CLOUD_BEAR = "#EF9A9A"

# Build candlestick segments (bullish/bearish)
bull_wicks, bear_wicks = [], []
bull_bodies, bear_bodies = [], []

for i in range(VIEW_START, VIEW_END):
    x = i - VIEW_START + 1
    candle = ohlc[i]
    wick = [(x, candle["low"]), (x, candle["high"]), None]
    body = [(x, candle["open"]), (x, candle["close"]), None]
    if candle["close"] >= candle["open"]:
        bull_wicks.extend(wick)
        bull_bodies.extend(body)
    else:
        bear_wicks.extend(wick)
        bear_bodies.extend(body)

# Ichimoku line points
tenkan_pts = [
    (i - VIEW_START + 1, float(tenkan_sen[i])) for i in range(VIEW_START, VIEW_END) if not np.isnan(tenkan_sen[i])
]
kijun_pts = [
    (i - VIEW_START + 1, float(kijun_sen[i])) for i in range(VIEW_START, VIEW_END) if not np.isnan(kijun_sen[i])
]

span_a_pts = []
span_b_pts = []
for i in range(VIEW_START, VIEW_END + SHIFT):
    x = i - VIEW_START + 1
    if i < len(senkou_a) and not np.isnan(senkou_a[i]):
        span_a_pts.append((x, float(senkou_a[i])))
    if i < len(senkou_b) and not np.isnan(senkou_b[i]):
        span_b_pts.append((x, float(senkou_b[i])))

chikou_pts = [
    (i - VIEW_START + 1, float(chikou_span[i])) for i in range(VIEW_START, VIEW_END) if not np.isnan(chikou_span[i])
]

# Price range for chart
all_prices = [d["high"] for d in ohlc[VIEW_START:VIEW_END]] + [d["low"] for d in ohlc[VIEW_START:VIEW_END]]
all_prices += [v for v in senkou_a[VIEW_START : VIEW_END + SHIFT] if not np.isnan(v)]
all_prices += [v for v in senkou_b[VIEW_START : VIEW_END + SHIFT] if not np.isnan(v)]
price_min, price_max = min(all_prices), max(all_prices)
price_pad = (price_max - price_min) * 0.05

# Style
custom_style = Style(
    background="#fefefe",
    plot_background="#f7f7f5",
    foreground="#2a2a2a",
    foreground_strong="#1a1a1a",
    foreground_subtle="#d8d8d8",
    colors=(BULL_CLR, BEAR_CLR, BULL_CLR, BEAR_CLR, TENKAN_CLR, KIJUN_CLR, SPAN_A_CLR, SPAN_B_CLR, CHIKOU_CLR),
    stroke_width=3,
    title_font_size=72,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=40,
    value_font_size=30,
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    legend_font_family="sans-serif",
    value_font_family="sans-serif",
)

# Chart
date_map = {i - VIEW_START + 1: dates[i] for i in range(VIEW_START, min(VIEW_END, len(dates)))}

chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="indicator-ichimoku \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Date",
    y_title="Price ($)",
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    allow_interruptions=True,
    range=(price_min - price_pad, price_max + price_pad),
    xrange=(0, total_x + 1),
    legend_box_size=26,
    margin=40,
    spacing=20,
    tooltip_border_radius=8,
    truncate_legend=-1,
    value_formatter=lambda x: f"${x:.2f}",
    legend_at_bottom=True,
)

label_positions = list(range(1, VIEW_END - VIEW_START + SHIFT + 1, 20))
chart.x_labels = label_positions
chart.x_value_formatter = lambda x: date_map[int(round(x))].strftime("%b %d") if int(round(x)) in date_map else ""

WICK_W, BODY_W = 22, 64
LINE_W = 5

# Wicks (hidden from legend)
chart.add(None, bull_wicks, stroke=True, show_dots=False, stroke_style={"width": WICK_W, "linecap": "butt"})
chart.add(None, bear_wicks, stroke=True, show_dots=False, stroke_style={"width": WICK_W, "linecap": "butt"})

# Bodies
chart.add(
    "Bullish Candle", bull_bodies, stroke=True, show_dots=False, stroke_style={"width": BODY_W, "linecap": "butt"}
)
chart.add(
    "Bearish Candle", bear_bodies, stroke=True, show_dots=False, stroke_style={"width": BODY_W, "linecap": "butt"}
)

# Ichimoku lines
chart.add(
    "Tenkan-sen (9)", tenkan_pts, stroke=True, show_dots=False, stroke_style={"width": LINE_W, "linecap": "round"}
)
chart.add("Kijun-sen (26)", kijun_pts, stroke=True, show_dots=False, stroke_style={"width": LINE_W, "linecap": "round"})
chart.add("Senkou A", span_a_pts, stroke=True, show_dots=False, stroke_style={"width": 3, "linecap": "round"})
chart.add("Senkou B", span_b_pts, stroke=True, show_dots=False, stroke_style={"width": 3, "linecap": "round"})
chart.add(
    "Chikou Span",
    chikou_pts,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 3, "linecap": "round", "dasharray": "12,6"},
)

# Render SVG and post-process for cairosvg compatibility
svg = chart.render(is_unicode=True)

# Apply stroke widths/linecaps inline (cairosvg ignores pygal's JS-based styling)
stroke_specs = [
    (WICK_W, "butt"),
    (WICK_W, "butt"),  # wicks
    (BODY_W, "butt"),
    (BODY_W, "butt"),  # bodies
    (LINE_W, "round"),
    (LINE_W, "round"),  # tenkan, kijun
    (3, "round"),
    (3, "round"),
    (3, "round"),  # spans + chikou
]
for sid, (w, cap) in enumerate(stroke_specs):
    svg = re.sub(
        rf'(class="series serie-{sid} color-{sid}"[^>]*>.*?)(class="line reactive nofill")',
        rf'\1\2 style="stroke-width:{w};stroke-linecap:{cap}"',
        svg,
        count=1,
        flags=re.DOTALL,
    )

# Inject Kumo cloud polygons into the SVG plot area
bg_rects = re.findall(r'<rect[^>]*width="([^"]*)"[^>]*height="([^"]*)"[^>]*class="background"', svg)
if len(bg_rects) >= 2:
    inner_w, inner_h = float(bg_rects[1][0]), float(bg_rects[1][1])
    x_min_data, x_max_data = 0, total_x + 1
    y_min_data, y_max_data = price_min - price_pad, price_max + price_pad
    x_range = x_max_data - x_min_data
    y_range = y_max_data - y_min_data

    span_a_dict = {pt[0]: pt[1] for pt in span_a_pts}
    span_b_dict = {pt[0]: pt[1] for pt in span_b_pts}
    common_x = sorted(set(span_a_dict) & set(span_b_dict))

    polys = []
    for k in range(len(common_x) - 1):
        x1, x2 = common_x[k], common_x[k + 1]
        if x2 - x1 > 2:
            continue
        a1, b1, a2, b2 = span_a_dict[x1], span_b_dict[x1], span_a_dict[x2], span_b_dict[x2]
        color = CLOUD_BULL if (a1 + a2) >= (b1 + b2) else CLOUD_BEAR
        pts = [(x1, a1), (x2, a2), (x2, b2), (x1, b1)]
        coords = " ".join(
            f"{(x - x_min_data) / x_range * inner_w:.1f},{inner_h - (y - y_min_data) / y_range * inner_h:.1f}"
            for x, y in pts
        )
        polys.append(f'<polygon points="{coords}" fill="{color}" fill-opacity="0.35" stroke="none" />')

    if polys:
        svg = svg.replace('<g class="series serie-0', "\n".join(polys) + '\n<g class="series serie-0')

# Save
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to="plot.png")
with open("plot.html", "w") as f:
    f.write(svg)
