""" pyplots.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: highcharts unknown | Python 3.14.3
Quality: 87/100 | Created: 2026-03-12
"""

import json
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from highcharts_stock.chart import Chart
from highcharts_stock.options import HighchartsStockOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - 200 trading days of simulated stock prices
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

# Generate trading dates (skip weekends)
start_date = datetime(2024, 1, 2)
dates = []
current_date = start_date
while len(dates) < n_days:
    if current_date.weekday() < 5:
        dates.append(current_date)
    current_date += timedelta(days=1)

timestamps = [int(d.timestamp() * 1000) for d in dates]

# Compute Ichimoku components
tenkan_period = 9
kijun_period = 26
senkou_b_period = 52
displacement = 26

# Tenkan-sen (conversion line): (9-period high + 9-period low) / 2
tenkan_sen = [None] * (tenkan_period - 1)
for i in range(tenkan_period - 1, n_days):
    s = i - tenkan_period + 1
    tenkan_sen.append(round((max(highs[s : s + tenkan_period]) + min(lows[s : s + tenkan_period])) / 2, 2))

# Kijun-sen (base line): (26-period high + 26-period low) / 2
kijun_sen = [None] * (kijun_period - 1)
for i in range(kijun_period - 1, n_days):
    s = i - kijun_period + 1
    kijun_sen.append(round((max(highs[s : s + kijun_period]) + min(lows[s : s + kijun_period])) / 2, 2))

# Senkou Span A: (Tenkan + Kijun) / 2, plotted 26 periods ahead
senkou_a_raw = []
for i in range(n_days):
    if tenkan_sen[i] is not None and kijun_sen[i] is not None:
        senkou_a_raw.append(round((tenkan_sen[i] + kijun_sen[i]) / 2, 2))
    else:
        senkou_a_raw.append(None)

# Senkou Span B: (52-period high + 52-period low) / 2, plotted 26 periods ahead
senkou_b_raw = [None] * (senkou_b_period - 1)
for i in range(senkou_b_period - 1, n_days):
    s = i - senkou_b_period + 1
    senkou_b_raw.append(round((max(highs[s : s + senkou_b_period]) + min(lows[s : s + senkou_b_period])) / 2, 2))

# Extend timestamps for future displacement
future_dates = []
future_date = dates[-1]
while len(future_dates) < displacement:
    future_date += timedelta(days=1)
    if future_date.weekday() < 5:
        future_dates.append(future_date)
future_timestamps = [int(d.timestamp() * 1000) for d in future_dates]
extended_timestamps = timestamps + future_timestamps

# Shifted Senkou spans (displaced 26 periods forward)
senkou_a_shifted = []
senkou_b_shifted = []
for i in range(n_days):
    shifted_idx = i + displacement
    if shifted_idx < len(extended_timestamps) and senkou_a_raw[i] is not None:
        senkou_a_shifted.append([extended_timestamps[shifted_idx], senkou_a_raw[i]])
    if shifted_idx < len(extended_timestamps) and senkou_b_raw[i] is not None:
        senkou_b_shifted.append([extended_timestamps[shifted_idx], senkou_b_raw[i]])

# Chikou Span: close plotted 26 periods behind
chikou_data = []
for i in range(n_days):
    past_idx = i - displacement
    if past_idx >= 0:
        chikou_data.append([timestamps[past_idx], closes[i]])

# OHLC data for candlestick
ohlc_data = [[timestamps[i], opens[i], highs[i], lows[i], closes[i]] for i in range(n_days)]

# Tenkan-sen and Kijun-sen line data
tenkan_data = [[timestamps[i], tenkan_sen[i]] for i in range(n_days) if tenkan_sen[i] is not None]
kijun_data = [[timestamps[i], kijun_sen[i]] for i in range(n_days) if kijun_sen[i] is not None]

# Build cloud area ranges (Senkou A vs B) for filled area
span_a_map = {pt[0]: pt[1] for pt in senkou_a_shifted}
span_b_map = {pt[0]: pt[1] for pt in senkou_b_shifted}
all_cloud_ts = sorted(set(span_a_map.keys()) & set(span_b_map.keys()))

cloud_bullish = []
cloud_bearish = []
for ts in all_cloud_ts:
    a_val = span_a_map[ts]
    b_val = span_b_map[ts]
    low_val = min(a_val, b_val)
    high_val = max(a_val, b_val)
    if a_val >= b_val:
        cloud_bullish.append([ts, low_val, high_val])
        cloud_bearish.append([ts, None, None])
    else:
        cloud_bearish.append([ts, low_val, high_val])
        cloud_bullish.append([ts, None, None])

# Detect Tenkan/Kijun crossover signals for flags
crossover_flags = []
for i in range(kijun_period, n_days):
    if tenkan_sen[i] is None or kijun_sen[i] is None or tenkan_sen[i - 1] is None or kijun_sen[i - 1] is None:
        continue
    prev_diff = tenkan_sen[i - 1] - kijun_sen[i - 1]
    curr_diff = tenkan_sen[i] - kijun_sen[i]
    if prev_diff <= 0 < curr_diff:
        crossover_flags.append(
            {"x": timestamps[i], "title": "\u25b2", "text": f"Bullish crossover at ${closes[i]:.2f}"}
        )
    elif prev_diff >= 0 > curr_diff:
        crossover_flags.append(
            {"x": timestamps[i], "title": "\u25bc", "text": f"Bearish crossover at ${closes[i]:.2f}"}
        )

# Colorblind-safe palette
BULLISH_COLOR = "#2E8B87"  # Teal
BEARISH_COLOR = "#D94F6B"  # Coral
BULLISH_LINE = "#1F6B67"
BEARISH_LINE = "#B03A55"

# Build chart using highcharts-stock Python API
chart = Chart.from_options(HighchartsStockOptions())
chart.container = "container"
chart.options.chart = {
    "type": "candlestick",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#FAFBFC",
    "marginBottom": 200,
    "spacingBottom": 30,
    "marginLeft": 200,
    "marginRight": 120,
    "marginTop": 180,
    "style": {"fontFamily": "'Segoe UI', Arial, sans-serif"},
}
chart.options.title = {
    "text": "indicator-ichimoku \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "60px", "fontWeight": "600", "color": "#1a1a2e", "letterSpacing": "0.5px"},
    "y": 65,
}
chart.options.subtitle = {
    "text": "Ichimoku Cloud overlay on 200 simulated trading days \u2014 crossover signals marked with flags",
    "style": {"fontSize": "36px", "color": "#666680", "fontWeight": "300"},
    "y": 120,
}
chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "42px", "color": "#444460", "fontWeight": "500"}, "margin": 25},
    "labels": {
        "style": {"fontSize": "32px", "color": "#666680"},
        "format": "{value:%b %Y}",
        "y": 40,
        "rotation": 0,
        "step": 2,
    },
    "gridLineWidth": 0,
    "lineWidth": 0,
    "tickWidth": 0,
    "crosshair": {"width": 2, "color": "rgba(100, 100, 120, 0.3)", "dashStyle": "Dash"},
}
chart.options.y_axis = {
    "title": {
        "text": "Price (USD)",
        "style": {"fontSize": "42px", "color": "#444460", "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#666680"}, "format": "${value:.0f}", "x": -15},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(100, 100, 120, 0.10)",
    "gridLineDashStyle": "Dot",
    "lineWidth": 0,
    "opposite": False,
    "tickWidth": 0,
}
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -40,
    "y": 60,
    "floating": True,
    "itemStyle": {"fontSize": "28px", "fontWeight": "400", "color": "#444460"},
    "symbolWidth": 40,
    "symbolRadius": 0,
    "itemMarginBottom": 8,
}
chart.options.tooltip = {
    "split": False,
    "shared": True,
    "style": {"fontSize": "26px"},
    "headerFormat": "<b>{point.x:%b %d, %Y}</b><br/>",
    "backgroundColor": "rgba(255, 255, 255, 0.96)",
    "borderColor": "#ccc",
    "borderRadius": 8,
    "shadow": {"color": "rgba(0, 0, 0, 0.15)", "offsetX": 2, "offsetY": 2, "width": 4},
}
chart.options.plot_options = {
    "candlestick": {
        "color": BEARISH_COLOR,
        "upColor": BULLISH_COLOR,
        "lineColor": BEARISH_LINE,
        "upLineColor": BULLISH_LINE,
        "lineWidth": 3,
        "pointWidth": 18,
        "tooltip": {
            "pointFormat": "O: ${point.open:.2f} H: ${point.high:.2f}<br/>"
            + "L: ${point.low:.2f} C: ${point.close:.2f}"
        },
    },
    "series": {"animation": False},
}
chart.options.range_selector = {"enabled": False}
chart.options.navigator = {"enabled": False}
chart.options.scrollbar = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.series = [
    {"type": "candlestick", "id": "dataseries", "name": "OHLC", "data": ohlc_data, "zIndex": 4},
    {
        "type": "line",
        "name": "Tenkan-sen (9)",
        "data": tenkan_data,
        "color": "#306998",
        "lineWidth": 4,
        "marker": {"enabled": False},
        "zIndex": 3,
        "enableMouseTracking": True,
        "tooltip": {"pointFormat": "Tenkan: <b>${point.y:.2f}</b><br/>"},
    },
    {
        "type": "line",
        "name": "Kijun-sen (26)",
        "data": kijun_data,
        "color": "#D35400",
        "lineWidth": 4,
        "marker": {"enabled": False},
        "zIndex": 3,
        "enableMouseTracking": True,
        "tooltip": {"pointFormat": "Kijun: <b>${point.y:.2f}</b><br/>"},
    },
    {
        "type": "line",
        "name": "Senkou Span A",
        "data": senkou_a_shifted,
        "color": "rgba(46, 139, 135, 0.6)",
        "lineWidth": 2,
        "marker": {"enabled": False},
        "zIndex": 1,
        "dashStyle": "ShortDot",
        "enableMouseTracking": False,
    },
    {
        "type": "line",
        "name": "Senkou Span B",
        "data": senkou_b_shifted,
        "color": "rgba(217, 79, 107, 0.6)",
        "lineWidth": 2,
        "marker": {"enabled": False},
        "zIndex": 1,
        "dashStyle": "ShortDot",
        "enableMouseTracking": False,
    },
    {
        "type": "line",
        "name": "Chikou Span",
        "data": chikou_data,
        "color": "#8E44AD",
        "lineWidth": 3,
        "marker": {"enabled": False},
        "zIndex": 2,
        "dashStyle": "Dash",
        "enableMouseTracking": True,
        "tooltip": {"pointFormat": "Chikou: <b>${point.y:.2f}</b><br/>"},
    },
    {
        "type": "arearange",
        "name": "Kumo (bullish)",
        "data": cloud_bullish,
        "color": "rgba(46, 139, 135, 0.22)",
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
        "color": "rgba(217, 79, 107, 0.22)",
        "lineWidth": 0,
        "marker": {"enabled": False},
        "zIndex": 0,
        "enableMouseTracking": False,
        "showInLegend": False,
    },
    {
        "type": "flags",
        "name": "Crossover Signals",
        "data": crossover_flags,
        "onSeries": "dataseries",
        "shape": "squarepin",
        "zIndex": 5,
        "style": "fontSize: 24px",
        "fillColor": "rgba(255, 255, 255, 0.92)",
        "lineColor": "#444460",
        "lineWidth": 2,
        "width": 40,
        "height": 30,
    },
]

# Serialize validated chart options to JSON for reliable inline rendering
chart_dict = chart.options.to_dict()
chart_dict["plotOptions"]["candlestick"]["lineColor"] = BEARISH_LINE
# Clean up artifacts from Python API serialization
chart_dict["plotOptions"]["candlestick"].pop("type", None)
chart_dict["plotOptions"]["series"].pop("type", None)
# margin array duplicates individual margin properties; keep both for clarity
chart_options_json = json.dumps(chart_dict)

# Download Highstock JS and highcharts-more (for arearange)
highstock_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highstock.js"
more_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js"

with urllib.request.urlopen(highstock_url, timeout=30) as response:
    highstock_js = response.read().decode("utf-8")
with urllib.request.urlopen(more_url, timeout=30) as response:
    more_js = response.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highstock_js}</script>
    <script>{more_js}</script>
</head>
<body style="margin:0; background-color: #FAFBFC;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.stockChart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
