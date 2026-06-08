"""anyplot.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-06-08
"""

import json
import os
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette, theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — semantic assignment for financial chart
BULLISH = "#009E73"  # Imprint pos 1 — brand green, also standard for up/gain
BEARISH = "#AE3030"  # Imprint pos 5 — matte red, semantic anchor for loss/error
TENKAN_COLOR = "#C475FD"  # Imprint pos 2 — lavender
KIJUN_COLOR = "#4467A3"  # Imprint pos 3 — blue
CHIKOU_COLOR = "#BD8233"  # Imprint pos 4 — ochre

# Data — 200 trading days of simulated stock prices
np.random.seed(42)
n_days = 200
start_price = 180.0

opens = [start_price]
highs = []
lows = []
closes = []

for i in range(n_days):
    open_price = opens[i] if i == 0 else closes[i - 1] + np.random.randn() * 0.3
    if i > 0:
        opens.append(open_price)
    daily_range = abs(np.random.randn() * 1.5) + 0.8
    trend = 0.05 * np.sin(2 * np.pi * i / 80)
    direction = 1 if np.random.rand() < (0.52 + trend) else -1
    close_price = open_price + direction * np.random.rand() * daily_range
    high_price = max(open_price, close_price) + abs(np.random.randn() * 0.4)
    low_price = min(open_price, close_price) - abs(np.random.randn() * 0.4)
    highs.append(round(high_price, 2))
    lows.append(round(low_price, 2))
    closes.append(round(close_price, 2))

opens = [round(o, 2) for o in opens]

start_date = datetime(2024, 1, 2)
dates = []
current_date = start_date
while len(dates) < n_days:
    if current_date.weekday() < 5:
        dates.append(current_date)
    current_date += timedelta(days=1)

timestamps = [int(d.timestamp() * 1000) for d in dates]

# Ichimoku indicators — standard (9, 26, 52) parameters
tenkan_period = 9
kijun_period = 26
senkou_b_period = 52
displacement = 26

tenkan_sen = [None] * (tenkan_period - 1)
for i in range(tenkan_period - 1, n_days):
    s = i - tenkan_period + 1
    tenkan_sen.append(round((max(highs[s : s + tenkan_period]) + min(lows[s : s + tenkan_period])) / 2, 2))

kijun_sen = [None] * (kijun_period - 1)
for i in range(kijun_period - 1, n_days):
    s = i - kijun_period + 1
    kijun_sen.append(round((max(highs[s : s + kijun_period]) + min(lows[s : s + kijun_period])) / 2, 2))

senkou_a_raw = [
    round((tenkan_sen[i] + kijun_sen[i]) / 2, 2) if (tenkan_sen[i] is not None and kijun_sen[i] is not None) else None
    for i in range(n_days)
]

senkou_b_raw = [None] * (senkou_b_period - 1)
for i in range(senkou_b_period - 1, n_days):
    s = i - senkou_b_period + 1
    senkou_b_raw.append(round((max(highs[s : s + senkou_b_period]) + min(lows[s : s + senkou_b_period])) / 2, 2))

future_dates = []
future_date = dates[-1]
while len(future_dates) < displacement:
    future_date += timedelta(days=1)
    if future_date.weekday() < 5:
        future_dates.append(future_date)
extended_timestamps = timestamps + [int(d.timestamp() * 1000) for d in future_dates]

# Shifted Senkou spans (displaced 26 periods forward) and Chikou (26 behind)
senkou_a_shifted = []
senkou_b_shifted = []
for i in range(n_days):
    idx = i + displacement
    if idx < len(extended_timestamps):
        if senkou_a_raw[i] is not None:
            senkou_a_shifted.append([extended_timestamps[idx], senkou_a_raw[i]])
        if senkou_b_raw[i] is not None:
            senkou_b_shifted.append([extended_timestamps[idx], senkou_b_raw[i]])

chikou_data = [[timestamps[i - displacement], closes[i]] for i in range(displacement, n_days)]
ohlc_data = [[timestamps[i], opens[i], highs[i], lows[i], closes[i]] for i in range(n_days)]
tenkan_data = [[timestamps[i], tenkan_sen[i]] for i in range(n_days) if tenkan_sen[i] is not None]
kijun_data = [[timestamps[i], kijun_sen[i]] for i in range(n_days) if kijun_sen[i] is not None]

# Build Kumo cloud arearange (bullish / bearish zones)
span_a_map = {pt[0]: pt[1] for pt in senkou_a_shifted}
span_b_map = {pt[0]: pt[1] for pt in senkou_b_shifted}
all_cloud_ts = sorted(set(span_a_map) & set(span_b_map))

cloud_bullish = []
cloud_bearish = []
for ts in all_cloud_ts:
    a, b = span_a_map[ts], span_b_map[ts]
    lo, hi = min(a, b), max(a, b)
    if a >= b:
        cloud_bullish.append([ts, lo, hi])
        cloud_bearish.append([ts, None, None])
    else:
        cloud_bearish.append([ts, lo, hi])
        cloud_bullish.append([ts, None, None])

# Tenkan / Kijun crossover signals
crossover_flags = []
for i in range(kijun_period, n_days):
    if any(v is None for v in [tenkan_sen[i], kijun_sen[i], tenkan_sen[i - 1], kijun_sen[i - 1]]):
        continue
    prev_diff = tenkan_sen[i - 1] - kijun_sen[i - 1]
    curr_diff = tenkan_sen[i] - kijun_sen[i]
    if prev_diff <= 0 < curr_diff:
        crossover_flags.append({"x": timestamps[i], "title": "▲", "text": f"Bullish crossover at ${closes[i]:.2f}"})
    elif prev_diff >= 0 > curr_diff:
        crossover_flags.append({"x": timestamps[i], "title": "▼", "text": f"Bearish crossover at ${closes[i]:.2f}"})

# Title length scaling (66px default at ~67 chars)
title = "indicator-ichimoku · python · highcharts · anyplot.ai"
title_px = f"{max(44, round(66 * 67 / max(len(title), 67)))}px"

# Chart options (direct JSON dict — camelCase for Highcharts JS, avoids Python API artifacts)
chart_options = {
    "chart": {
        "width": 3200,
        "height": 1800,
        "backgroundColor": PAGE_BG,
        "marginTop": 90,
        "marginBottom": 210,
        "marginLeft": 130,
        "marginRight": 60,
        "style": {"fontFamily": "Arial, sans-serif"},
    },
    "title": {"text": title, "style": {"fontSize": title_px, "color": INK, "fontWeight": "600"}, "margin": 16},
    "subtitle": {
        "text": "Ichimoku Cloud on 200 simulated trading days — Tenkan/Kijun crossover signals marked",
        "style": {"fontSize": "36px", "color": INK_MUTED},
        "margin": 10,
    },
    "xAxis": {
        "type": "datetime",
        "title": {"text": "Date", "style": {"fontSize": "56px", "color": INK}, "margin": 14},
        "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "{value:%b '%y}"},
        "tickInterval": 30 * 24 * 3600 * 1000,
        "gridLineWidth": 0,
        "lineColor": INK_SOFT,
        "lineWidth": 1,
        "tickColor": INK_SOFT,
        "tickWidth": 1,
    },
    "yAxis": {
        "title": {"text": "Price (USD)", "style": {"fontSize": "56px", "color": INK}, "margin": 14},
        "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "${value:.0f}", "x": -8},
        "gridLineColor": GRID,
        "gridLineWidth": 1,
        "lineWidth": 0,
        "tickWidth": 0,
    },
    "legend": {
        "enabled": True,
        "align": "center",
        "verticalAlign": "bottom",
        "layout": "horizontal",
        "floating": False,
        "itemStyle": {"fontSize": "40px", "fontWeight": "400", "color": INK_SOFT},
        "backgroundColor": "transparent",
        "borderWidth": 0,
        "symbolWidth": 30,
        "symbolRadius": 0,
        "itemMarginTop": 10,
        "itemMarginBottom": 0,
    },
    "tooltip": {
        "shared": True,
        "style": {"fontSize": "36px", "color": INK},
        "headerFormat": "<b>{point.x:%b %d, %Y}</b><br/>",
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderRadius": 4,
    },
    "plotOptions": {
        "candlestick": {
            "color": BEARISH,
            "upColor": BULLISH,
            "lineColor": BEARISH,
            "upLineColor": BULLISH,
            "lineWidth": 2,
            "pointWidth": 10,
            "tooltip": {
                "pointFormat": "O: ${point.open:.2f}  H: ${point.high:.2f}  L: ${point.low:.2f}  C: ${point.close:.2f}<br/>"
            },
        },
        "series": {"animation": False},
    },
    "rangeSelector": {"enabled": False},
    "navigator": {"enabled": False},
    "scrollbar": {"enabled": False},
    "credits": {"enabled": False},
    "series": [
        {"type": "candlestick", "id": "price", "name": "OHLC", "data": ohlc_data, "zIndex": 4},
        {
            "type": "line",
            "name": "Tenkan-sen (9)",
            "data": tenkan_data,
            "color": TENKAN_COLOR,
            "lineWidth": 3,
            "marker": {"enabled": False},
            "zIndex": 3,
            "tooltip": {"pointFormat": "Tenkan: <b>${point.y:.2f}</b><br/>"},
        },
        {
            "type": "line",
            "name": "Kijun-sen (26)",
            "data": kijun_data,
            "color": KIJUN_COLOR,
            "lineWidth": 3,
            "marker": {"enabled": False},
            "zIndex": 3,
            "tooltip": {"pointFormat": "Kijun: <b>${point.y:.2f}</b><br/>"},
        },
        {
            "type": "line",
            "name": "Chikou Span",
            "data": chikou_data,
            "color": CHIKOU_COLOR,
            "lineWidth": 2,
            "marker": {"enabled": False},
            "zIndex": 2,
            "dashStyle": "Dash",
            "tooltip": {"pointFormat": "Chikou: <b>${point.y:.2f}</b><br/>"},
        },
        {
            "type": "line",
            "name": "Senkou Span A",
            "data": senkou_a_shifted,
            "color": BULLISH,
            "lineWidth": 1,
            "marker": {"enabled": False},
            "zIndex": 1,
            "dashStyle": "ShortDot",
            "enableMouseTracking": False,
        },
        {
            "type": "line",
            "name": "Senkou Span B",
            "data": senkou_b_shifted,
            "color": BEARISH,
            "lineWidth": 1,
            "marker": {"enabled": False},
            "zIndex": 1,
            "dashStyle": "ShortDot",
            "enableMouseTracking": False,
        },
        {
            "type": "arearange",
            "name": "Kumo (bullish)",
            "data": cloud_bullish,
            "color": BULLISH,
            "fillColor": "rgba(0,158,115,0.20)",
            "lineWidth": 0,
            "marker": {"enabled": False},
            "zIndex": 0,
            "enableMouseTracking": False,
            "showInLegend": False,
        },
        {
            "type": "arearange",
            "name": "Kumo (bearish)",
            "data": cloud_bearish,
            "color": BEARISH,
            "fillColor": "rgba(174,48,48,0.20)",
            "lineWidth": 0,
            "marker": {"enabled": False},
            "zIndex": 0,
            "enableMouseTracking": False,
            "showInLegend": False,
        },
        {
            "type": "flags",
            "name": "Signals",
            "data": crossover_flags,
            "onSeries": "price",
            "shape": "squarepin",
            "zIndex": 5,
            "fillColor": ELEVATED_BG,
            "lineColor": INK_SOFT,
            "lineWidth": 1,
            "width": 30,
            "height": 22,
            "style": {"fontSize": "26px", "color": INK},
        },
    ],
}

chart_options_json = json.dumps(chart_options)

# Download Highstock JS and highcharts-more (required for candlestick, flags, arearange)
highstock_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highstock.js"
more_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js"

with urllib.request.urlopen(highstock_url, timeout=30) as r:
    highstock_js = r.read().decode("utf-8")
with urllib.request.urlopen(more_url, timeout=30) as r:
    more_js = r.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highstock_js}</script>
    <script>{more_js}</script>
</head>
<body style="margin:0;padding:0;background:{PAGE_BG};">
    <div id="container" style="width:3200px;height:1800px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.stockChart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 3200×1800 — belt-and-braces for ±1-2 px rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
