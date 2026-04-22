""" pyplots.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2026-01-01
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


# Data - Generate 60 trading days of OHLC data
np.random.seed(42)

# Start date and generate trading days (skip weekends)
start_date = datetime(2024, 9, 2)  # A Monday
dates = []
current_date = start_date
while len(dates) < 60:
    if current_date.weekday() < 5:  # Monday to Friday
        dates.append(current_date)
    current_date += timedelta(days=1)

# Generate realistic stock price movements
n_days = 60
initial_price = 150.0
returns = np.random.normal(0.001, 0.02, n_days)  # Daily returns with slight upward bias
close_prices = initial_price * np.cumprod(1 + returns)

# Generate OHLC from close prices
open_prices = np.zeros(n_days)
high_prices = np.zeros(n_days)
low_prices = np.zeros(n_days)
volumes = np.zeros(n_days)

open_prices[0] = initial_price
for i in range(n_days):
    if i > 0:
        # Open is close of previous day with small gap
        gap = np.random.normal(0, close_prices[i - 1] * 0.005)
        open_prices[i] = close_prices[i - 1] + gap

    # High and low based on volatility
    volatility = abs(close_prices[i] - open_prices[i]) + np.random.uniform(0.5, 2.0)
    if close_prices[i] >= open_prices[i]:  # Bullish candle
        high_prices[i] = max(open_prices[i], close_prices[i]) + np.random.uniform(0.3, volatility)
        low_prices[i] = min(open_prices[i], close_prices[i]) - np.random.uniform(0.2, volatility * 0.7)
    else:  # Bearish candle
        high_prices[i] = max(open_prices[i], close_prices[i]) + np.random.uniform(0.2, volatility * 0.7)
        low_prices[i] = min(open_prices[i], close_prices[i]) - np.random.uniform(0.3, volatility)

    # Ensure high >= max(open, close) and low <= min(open, close)
    high_prices[i] = max(high_prices[i], open_prices[i], close_prices[i])
    low_prices[i] = min(low_prices[i], open_prices[i], close_prices[i])

    # Volume: higher on days with larger price moves
    base_volume = 5_000_000
    move_factor = 1 + abs(close_prices[i] - open_prices[i]) / open_prices[i] * 20
    volumes[i] = int(base_volume * move_factor * np.random.uniform(0.6, 1.4))

# Convert dates to JavaScript timestamps (milliseconds since epoch)
timestamps = [int(d.timestamp() * 1000) for d in dates]

# Prepare data for Highcharts
ohlc_data = []
volume_data = []

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
    # Volume color matches candle direction
    color = "#306998" if close_prices[i] >= open_prices[i] else "#E74C3C"
    volume_data.append({"x": timestamps[i], "y": int(volumes[i]), "color": color})

# Convert to JSON for JavaScript
ohlc_json = json.dumps(ohlc_data)
volume_json = json.dumps(volume_data)

# Chart configuration using Highstock (for synchronized charts)
chart_js = """
Highcharts.stockChart('container', {
    chart: {
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff',
        spacingBottom: 100,
        style: {
            fontFamily: 'Arial, sans-serif'
        }
    },

    title: {
        text: 'candlestick-volume \\u00b7 highcharts \\u00b7 pyplots.ai',
        style: {
            fontSize: '48px',
            fontWeight: 'bold'
        }
    },

    rangeSelector: {
        enabled: false
    },

    navigator: {
        enabled: false
    },

    scrollbar: {
        enabled: false
    },

    credits: {
        enabled: false
    },

    yAxis: [{
        labels: {
            align: 'right',
            x: -10,
            style: {
                fontSize: '24px'
            },
            formatter: function() {
                return '$' + this.value.toFixed(0);
            }
        },
        title: {
            text: 'Price (USD)',
            style: {
                fontSize: '28px'
            }
        },
        height: '70%',
        lineWidth: 2,
        resize: {
            enabled: false
        },
        gridLineWidth: 1,
        gridLineColor: '#E0E0E0'
    }, {
        labels: {
            align: 'right',
            x: -10,
            style: {
                fontSize: '24px'
            },
            formatter: function() {
                return (this.value / 1000000).toFixed(1) + 'M';
            }
        },
        title: {
            text: 'Volume',
            style: {
                fontSize: '28px'
            }
        },
        top: '72%',
        height: '22%',
        offset: 0,
        lineWidth: 2,
        gridLineWidth: 1,
        gridLineColor: '#E0E0E0'
    }],

    xAxis: {
        type: 'datetime',
        labels: {
            style: {
                fontSize: '28px'
            },
            format: '{value:%b %d}',
            y: 40
        },
        crosshair: {
            width: 2,
            color: '#888888',
            snap: false
        },
        gridLineWidth: 1,
        gridLineColor: '#E0E0E0',
        lineWidth: 2
    },

    tooltip: {
        split: true,
        style: {
            fontSize: '20px'
        }
    },

    plotOptions: {
        candlestick: {
            color: '#E74C3C',
            upColor: '#306998',
            lineColor: '#E74C3C',
            upLineColor: '#306998',
            lineWidth: 2
        },
        column: {
            borderWidth: 0
        }
    },

    series: [{
        type: 'candlestick',
        name: 'Stock Price',
        data: OHLC_DATA_PLACEHOLDER,
        yAxis: 0
    }, {
        type: 'column',
        name: 'Volume',
        data: VOLUME_DATA_PLACEHOLDER,
        yAxis: 1
    }]
});
"""

# Replace data placeholders
chart_js = chart_js.replace("OHLC_DATA_PLACEHOLDER", ohlc_json)
chart_js = chart_js.replace("VOLUME_DATA_PLACEHOLDER", volume_json)

# Download Highcharts and Highstock JS
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
