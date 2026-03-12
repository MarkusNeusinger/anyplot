""" pyplots.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 74/100 | Created: 2026-03-12
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

# Colors
BULL_CLR, BEAR_CLR = "#2271B3", "#D66B27"
TENKAN_CLR, KIJUN_CLR = "#E6550D", "#306998"
SPAN_A_CLR, SPAN_B_CLR = "#2CA02C", "#D62728"
CHIKOU_CLR = "#9467BD"
CLOUD_BULL = "#2CA02C"
CLOUD_BEAR = "#D62728"

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
    background="white",
    plot_background="#fafaf8",
    foreground="#2a2a2a",
    foreground_strong="#1a1a1a",
    foreground_subtle="#e0e0e0",
    colors=(BULL_CLR, BEAR_CLR, BULL_CLR, BEAR_CLR, TENKAN_CLR, KIJUN_CLR, SPAN_A_CLR, SPAN_B_CLR, CHIKOU_CLR),
    title_font_size=72,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=40,
    value_font_size=30,
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

WICK_W, BODY_W = 10, 28
LINE_W = 5

# Wicks (hidden from legend)
chart.add(None, bull_wicks, stroke=True, show_dots=False, stroke_style={"width": WICK_W, "linecap": "butt"})
chart.add(None, bear_wicks, stroke=True, show_dots=False, stroke_style={"width": WICK_W, "linecap": "butt"})

# Bodies
chart.add("Bullish", bull_bodies, stroke=True, show_dots=False, stroke_style={"width": BODY_W, "linecap": "butt"})
chart.add("Bearish", bear_bodies, stroke=True, show_dots=False, stroke_style={"width": BODY_W, "linecap": "butt"})

# Ichimoku lines
chart.add(
    "Tenkan-sen (9)", tenkan_pts, stroke=True, show_dots=False, stroke_style={"width": LINE_W, "linecap": "round"}
)
chart.add("Kijun-sen (26)", kijun_pts, stroke=True, show_dots=False, stroke_style={"width": LINE_W, "linecap": "round"})
chart.add("Senkou A", span_a_pts, stroke=True, show_dots=False, stroke_style={"width": 4, "linecap": "round"})
chart.add("Senkou B", span_b_pts, stroke=True, show_dots=False, stroke_style={"width": 4, "linecap": "round"})
chart.add(
    "Chikou Span",
    chikou_pts,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 4, "linecap": "round", "dasharray": "12,6"},
)

# Render SVG and post-process
svg = chart.render(is_unicode=True)

# Inline stroke styles for cairosvg compatibility
series_strokes = {
    0: (WICK_W, "butt"),
    1: (WICK_W, "butt"),
    2: (BODY_W, "butt"),
    3: (BODY_W, "butt"),
    4: (LINE_W, "round"),
    5: (LINE_W, "round"),
    6: (4, "round"),
    7: (4, "round"),
    8: (4, "round"),
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

# Inject Kumo cloud fill as SVG polygons
# Extract plot area: pygal uses <g transform="translate(X, Y)" class="plot">
# with inner background rect for dimensions
translate_match = re.search(r'translate\(([0-9.]+),\s*([0-9.]+)\)[^>]*class="plot"', svg)
bg_rects = re.findall(
    r'<rect[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*width="([^"]*)"[^>]*height="([^"]*)"[^>]*class="background"', svg
)

if translate_match and len(bg_rects) >= 2:
    plot_tx = float(translate_match.group(1))
    plot_ty = float(translate_match.group(2))
    inner_w = float(bg_rects[1][2])
    inner_h = float(bg_rects[1][3])

    x_min_data, x_max_data = 0, total_x + 1
    y_min_data, y_max_data = price_min - price_pad, price_max + price_pad

    span_a_dict = {pt[0]: pt[1] for pt in span_a_pts}
    span_b_dict = {pt[0]: pt[1] for pt in span_b_pts}
    common_x = sorted(set(span_a_dict.keys()) & set(span_b_dict.keys()))

    if common_x:
        cloud_polygons = []
        for k in range(len(common_x) - 1):
            x1, x2 = common_x[k], common_x[k + 1]
            if x2 - x1 > 2:
                continue
            a1, b1 = span_a_dict[x1], span_b_dict[x1]
            a2, b2 = span_a_dict[x2], span_b_dict[x2]

            color = CLOUD_BULL if (a1 + a2) / 2 >= (b1 + b2) / 2 else CLOUD_BEAR

            # Map to SVG coordinates (inside the plot group's local coordinate system)
            sx1 = (x1 - x_min_data) / (x_max_data - x_min_data) * inner_w
            sx2 = (x2 - x_min_data) / (x_max_data - x_min_data) * inner_w
            sa1 = inner_h - (a1 - y_min_data) / (y_max_data - y_min_data) * inner_h
            sb1 = inner_h - (b1 - y_min_data) / (y_max_data - y_min_data) * inner_h
            sa2 = inner_h - (a2 - y_min_data) / (y_max_data - y_min_data) * inner_h
            sb2 = inner_h - (b2 - y_min_data) / (y_max_data - y_min_data) * inner_h

            poly = (
                f'<polygon points="{sx1:.1f},{sa1:.1f} {sx2:.1f},{sa2:.1f} '
                f'{sx2:.1f},{sb2:.1f} {sx1:.1f},{sb1:.1f}" '
                f'fill="{color}" fill-opacity="0.22" stroke="none" />'
            )
            cloud_polygons.append(poly)

        # Insert cloud polygons inside the plot group, before the series
        cloud_svg = "\n".join(cloud_polygons)
        svg = svg.replace('<g class="series serie-0', cloud_svg + '\n<g class="series serie-0')

# Save
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to="plot.png")
with open("plot.html", "w") as f:
    f.write(svg)
