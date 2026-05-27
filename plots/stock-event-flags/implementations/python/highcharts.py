"""anyplot.ai
stock-event-flags: Stock Chart with Event Flags
Library: highcharts unknown | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-27
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.22)" if THEME == "light" else "rgba(240,239,232,0.22)"

# anyplot categorical palette
ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data
np.random.seed(42)

start_date = datetime(2024, 1, 2)
dates = []
current_date = start_date
while len(dates) < 120:
    if current_date.weekday() < 5:
        dates.append(current_date)
    current_date += timedelta(days=1)

n_days = 120
initial_price = 180.0
returns = np.random.normal(0.0008, 0.018, n_days)
close_prices = initial_price * np.cumprod(1 + returns)

open_prices = np.zeros(n_days)
high_prices = np.zeros(n_days)
low_prices = np.zeros(n_days)

open_prices[0] = initial_price
for i in range(n_days):
    if i > 0:
        gap = np.random.normal(0, close_prices[i - 1] * 0.003)
        open_prices[i] = close_prices[i - 1] + gap
    volatility = abs(close_prices[i] - open_prices[i]) + np.random.uniform(0.3, 1.5)
    if close_prices[i] >= open_prices[i]:
        high_prices[i] = max(open_prices[i], close_prices[i]) + np.random.uniform(0.2, volatility)
        low_prices[i] = min(open_prices[i], close_prices[i]) - np.random.uniform(0.1, volatility * 0.6)
    else:
        high_prices[i] = max(open_prices[i], close_prices[i]) + np.random.uniform(0.1, volatility * 0.6)
        low_prices[i] = min(open_prices[i], close_prices[i]) - np.random.uniform(0.2, volatility)
    high_prices[i] = max(high_prices[i], open_prices[i], close_prices[i])
    low_prices[i] = min(low_prices[i], open_prices[i], close_prices[i])

timestamps = [int(d.timestamp() * 1000) for d in dates]

ohlc_data = [
    [
        timestamps[i],
        round(open_prices[i], 2),
        round(high_prices[i], 2),
        round(low_prices[i], 2),
        round(close_prices[i], 2),
    ]
    for i in range(n_days)
]

# Events with anyplot palette colors (semantic exception: bull=#009E73, bear=#AE3030 for candlestick)
events = [
    {"date": dates[15], "type": "earnings", "label": "Q4", "title": "Q4 Earnings Beat"},
    {"date": dates[30], "type": "dividend", "label": "D", "title": "Dividend $0.88"},
    {"date": dates[45], "type": "news", "label": "N", "title": "Product Launch"},
    {"date": dates[60], "type": "earnings", "label": "Q1", "title": "Q1 Earnings"},
    {"date": dates[75], "type": "split", "label": "S", "title": "2:1 Stock Split"},
    {"date": dates[90], "type": "dividend", "label": "D", "title": "Dividend $0.92"},
    {"date": dates[105], "type": "news", "label": "N", "title": "Partnership Announced"},
]

# Flag series colors: palette positions 2-6 (position 1 used for bullish, 5 for bearish)
event_styles = {
    "earnings": {"color": ANYPLOT_PALETTE[1], "shape": "squarepin", "text_color": "#ffffff"},
    "dividend": {"color": ANYPLOT_PALETTE[2], "shape": "flag", "text_color": "#ffffff"},
    "news": {"color": ANYPLOT_PALETTE[3], "shape": "flag", "text_color": "#ffffff"},
    "split": {"color": ANYPLOT_PALETTE[5], "shape": "circlepin", "text_color": "#1A1A17"},
}

flags_by_type = {}
for event in events:
    etype = event["type"]
    if etype not in flags_by_type:
        flags_by_type[etype] = []
    ts = int(event["date"].timestamp() * 1000)
    flags_by_type[etype].append({"x": ts, "title": event["label"], "text": event["title"]})

y_offsets = {"earnings": -80, "dividend": -115, "split": -150, "news": -95}
flag_series = []
for etype, flags in flags_by_type.items():
    style = event_styles[etype]
    flag_series.append(
        {
            "type": "flags",
            "name": etype.capitalize(),
            "data": flags,
            "onSeries": "price",
            "shape": style["shape"],
            "color": style["color"],
            "fillColor": style["color"],
            "style": {"color": style["text_color"], "fontSize": "34px", "fontWeight": "bold"},
            "width": 76,
            "height": 46,
            "y": y_offsets.get(etype, -80),
            "lineWidth": 2,
            "lineColor": style["color"],
            "allowOverlapX": False,
            "showInLegend": True,
        }
    )

ohlc_json = json.dumps(ohlc_data)
flag_series_json = json.dumps(flag_series)

# Vertical dashed connector lines from each flag to the price level
event_plot_lines = [
    {"value": int(event["date"].timestamp() * 1000), "color": INK_SOFT, "dashStyle": "Dash", "width": 2, "zIndex": 1}
    for event in events
]
event_plot_lines_json = json.dumps(event_plot_lines)

chart_js = f"""
Highcharts.stockChart('container', {{
    chart: {{
        width: 3200,
        height: 1800,
        backgroundColor: '{PAGE_BG}',
        spacingTop: 60,
        spacingBottom: 100,
        spacingLeft: 60,
        spacingRight: 60,
        marginBottom: 280,
        style: {{
            fontFamily: 'Arial, sans-serif',
            color: '{INK}'
        }}
    }},

    title: {{
        text: 'stock-event-flags · python · highcharts · anyplot.ai',
        style: {{
            fontSize: '66px',
            fontWeight: 'bold',
            color: '{INK}'
        }},
        y: 40
    }},

    subtitle: {{
        text: 'Technology Stock 2024 · Earnings, Dividends, Stock Split, and News Events',
        style: {{
            fontSize: '38px',
            color: '{INK_SOFT}'
        }}
    }},

    rangeSelector: {{
        enabled: false
    }},

    navigator: {{
        enabled: false
    }},

    scrollbar: {{
        enabled: false
    }},

    credits: {{
        enabled: false
    }},

    legend: {{
        enabled: true,
        layout: 'horizontal',
        align: 'center',
        verticalAlign: 'bottom',
        itemStyle: {{
            fontSize: '44px',
            fontWeight: 'normal',
            color: '{INK_SOFT}'
        }},
        itemMarginTop: 8,
        itemMarginBottom: 8,
        symbolHeight: 22,
        symbolWidth: 22,
        symbolRadius: 11,
        backgroundColor: '{ELEVATED_BG}',
        borderWidth: 1,
        borderColor: '{INK_SOFT}',
        padding: 14
    }},

    yAxis: {{
        opposite: false,
        labels: {{
            align: 'right',
            x: -10,
            style: {{
                fontSize: '44px',
                color: '{INK_SOFT}'
            }},
            formatter: function() {{
                return '$' + this.value.toFixed(0);
            }}
        }},
        title: {{
            text: 'Price (USD)',
            style: {{
                fontSize: '56px',
                color: '{INK}'
            }},
            margin: 20,
            rotation: 270
        }},
        lineWidth: 1,
        lineColor: '{INK_SOFT}',
        gridLineWidth: 1,
        gridLineColor: '{GRID}',
        tickColor: '{INK_SOFT}',
        plotLines: [{{
            value: {round(initial_price, 2)},
            color: '{INK_SOFT}',
            dashStyle: 'dash',
            width: 2,
            label: {{
                text: 'Starting Price',
                align: 'right',
                style: {{
                    fontSize: '30px',
                    color: '{INK_SOFT}'
                }}
            }}
        }}]
    }},

    xAxis: {{
        type: 'datetime',
        labels: {{
            style: {{
                fontSize: '44px',
                color: '{INK_SOFT}'
            }},
            format: '{{value:%b %d}}',
            rotation: -45,
            align: 'right',
            y: 18
        }},
        plotLines: {event_plot_lines_json},
        tickInterval: 14 * 24 * 3600 * 1000,
        crosshair: {{
            width: 1,
            color: '{INK_SOFT}',
            snap: false
        }},
        gridLineWidth: 1,
        gridLineColor: '{GRID}',
        lineWidth: 1,
        lineColor: '{INK_SOFT}',
        tickColor: '{INK_SOFT}',
        offset: 0
    }},

    tooltip: {{
        split: false,
        shared: true,
        style: {{
            fontSize: '34px',
            color: '{INK}'
        }},
        backgroundColor: '{ELEVATED_BG}',
        borderColor: '{INK_SOFT}',
        dateTimeLabelFormats: {{
            day: '%A, %b %e, %Y'
        }}
    }},

    plotOptions: {{
        candlestick: {{
            color: '#AE3030',
            upColor: '#009E73',
            lineColor: '#AE3030',
            upLineColor: '#009E73',
            lineWidth: 2
        }},
        flags: {{
            lineWidth: 2,
            states: {{
                hover: {{
                    fillColor: '{ELEVATED_BG}'
                }}
            }}
        }}
    }},

    series: [{{
        type: 'candlestick',
        name: 'Stock Price',
        id: 'price',
        data: {ohlc_json},
        showInLegend: true
    }}].concat({flag_series_json})
}});
"""

# Download Highstock JS (includes flags series module) with CDN fallbacks
cdn_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/highstock.js",
    "https://unpkg.com/highcharts@11/highstock.js",
    "https://code.highcharts.com/stock/highstock.js",
]

highcharts_js = None
for url in cdn_urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
                break
        except (urllib.error.URLError, urllib.error.HTTPError):
            if attempt == 0:
                time.sleep(1)
    if highcharts_js:
        break

if not highcharts_js:
    raise RuntimeError("Could not download Highstock from any CDN")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>
    {chart_js}
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

_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
