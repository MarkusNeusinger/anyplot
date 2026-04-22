""" pyplots.ai
stock-event-flags: Stock Chart with Event Flags
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-21
"""

import json
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Generate 120 trading days of stock price data
np.random.seed(42)

# Start date and generate trading days (skip weekends)
start_date = datetime(2024, 1, 2)  # A Tuesday
dates = []
current_date = start_date
while len(dates) < 120:
    if current_date.weekday() < 5:  # Monday to Friday
        dates.append(current_date)
    current_date += timedelta(days=1)

# Generate realistic stock price movements
n_days = 120
initial_price = 180.0
returns = np.random.normal(0.0008, 0.018, n_days)  # Daily returns with slight upward bias
close_prices = initial_price * np.cumprod(1 + returns)

# Generate OHLC from close prices
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

# Convert dates to JavaScript timestamps (milliseconds since epoch)
timestamps = [int(d.timestamp() * 1000) for d in dates]

# Prepare OHLC data for Highcharts
ohlc_data = []
for i in range(n_days):
    ohlc_data.append(
        [
            timestamps[i],
            round(open_prices[i], 2),
            round(high_prices[i], 2),
            round(low_prices[i], 2),
            round(close_prices[i], 2),
        ]
    )

# Define events with different types
events = [
    {"date": dates[15], "type": "earnings", "label": "Q4", "title": "Q4 Earnings Beat"},
    {"date": dates[30], "type": "dividend", "label": "D", "title": "Dividend $0.88"},
    {"date": dates[45], "type": "news", "label": "N", "title": "Product Launch"},
    {"date": dates[60], "type": "earnings", "label": "Q1", "title": "Q1 Earnings"},
    {"date": dates[75], "type": "split", "label": "S", "title": "2:1 Stock Split"},
    {"date": dates[90], "type": "dividend", "label": "D", "title": "Dividend $0.92"},
    {"date": dates[105], "type": "news", "label": "N", "title": "Partnership Announced"},
]

# Event colors and shapes by type
event_styles = {
    "earnings": {"color": "#306998", "shape": "squarepin"},
    "dividend": {"color": "#27AE60", "shape": "flag"},
    "split": {"color": "#9B59B6", "shape": "circlepin"},
    "news": {"color": "#FFD43B", "shape": "flag"},
}

# Create flags data grouped by event type for different series
flags_by_type = {}
for event in events:
    etype = event["type"]
    if etype not in flags_by_type:
        flags_by_type[etype] = []
    ts = int(event["date"].timestamp() * 1000)
    flags_by_type[etype].append({"x": ts, "title": event["label"], "text": event["title"]})

# Build flag series configuration with larger flags and visible connector lines
flag_series = []
y_offsets = {"earnings": -100, "dividend": -140, "split": -180, "news": -120}
for etype, flags in flags_by_type.items():
    style = event_styles[etype]
    series_config = {
        "type": "flags",
        "name": etype.capitalize(),
        "data": flags,
        "onSeries": "price",
        "shape": style["shape"],
        "color": style["color"],
        "fillColor": style["color"],
        "style": {"color": "#ffffff" if etype != "news" else "#333333", "fontSize": "22px", "fontWeight": "bold"},
        "width": 90,
        "height": 60,
        "y": y_offsets.get(etype, -100),
        "lineWidth": 3,
        "lineColor": style["color"],
        "allowOverlapX": False,
        "showInLegend": True,
    }
    flag_series.append(series_config)

# Convert to JSON for JavaScript
ohlc_json = json.dumps(ohlc_data)
flag_series_json = json.dumps(flag_series)

# Chart configuration using Highstock
chart_js = f"""
Highcharts.stockChart('container', {{
    chart: {{
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff',
        spacingTop: 80,
        spacingBottom: 200,
        spacingLeft: 100,
        spacingRight: 100,
        marginBottom: 350,
        style: {{
            fontFamily: 'Arial, sans-serif'
        }}
    }},

    title: {{
        text: 'stock-event-flags \\u00b7 highcharts \\u00b7 pyplots.ai',
        style: {{
            fontSize: '56px',
            fontWeight: 'bold'
        }},
        y: 50
    }},

    subtitle: {{
        text: 'Stock Price with Earnings, Dividends, Splits, and News Events',
        style: {{
            fontSize: '32px',
            color: '#666666'
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
        y: 60,
        floating: false,
        itemStyle: {{
            fontSize: '28px',
            fontWeight: 'normal'
        }},
        itemMarginTop: 15,
        itemMarginBottom: 15,
        symbolHeight: 28,
        symbolWidth: 28,
        symbolRadius: 14,
        backgroundColor: '#ffffff',
        borderWidth: 1,
        borderColor: '#E0E0E0',
        padding: 20
    }},

    yAxis: {{
        opposite: false,
        labels: {{
            align: 'right',
            x: -10,
            style: {{
                fontSize: '28px'
            }},
            formatter: function() {{
                return '$' + this.value.toFixed(0);
            }}
        }},
        title: {{
            text: 'Price (USD)',
            style: {{
                fontSize: '32px'
            }},
            margin: 20,
            rotation: 270
        }},
        lineWidth: 2,
        gridLineWidth: 1,
        gridLineColor: '#E0E0E0',
        plotLines: [{{
            value: {round(initial_price, 2)},
            color: '#888888',
            dashStyle: 'dash',
            width: 3,
            label: {{
                text: 'Starting Price',
                align: 'right',
                style: {{
                    fontSize: '22px',
                    color: '#888888'
                }}
            }}
        }}]
    }},

    xAxis: {{
        type: 'datetime',
        labels: {{
            style: {{
                fontSize: '28px'
            }},
            format: '{{value:%b %d}}',
            y: 35,
            rotation: 0
        }},
        tickInterval: 14 * 24 * 3600 * 1000,
        crosshair: {{
            width: 2,
            color: '#888888',
            snap: false
        }},
        gridLineWidth: 1,
        gridLineColor: '#E0E0E0',
        lineWidth: 2,
        offset: 0
    }},

    tooltip: {{
        split: false,
        shared: true,
        style: {{
            fontSize: '22px'
        }},
        dateTimeLabelFormats: {{
            day: '%A, %b %e, %Y'
        }}
    }},

    plotOptions: {{
        candlestick: {{
            color: '#E74C3C',
            upColor: '#306998',
            lineColor: '#E74C3C',
            upLineColor: '#306998',
            lineWidth: 2
        }},
        flags: {{
            lineWidth: 3,
            lineColor: '#555555',
            states: {{
                hover: {{
                    fillColor: '#FCFFC5'
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

# Download Highstock JS
highcharts_url = "https://code.highcharts.com/stock/highstock.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    {chart_js}
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot using Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(8)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
