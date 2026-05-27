""" anyplot.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-16
"""

import json
import os
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

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

# Generate realistic stock price movements with varied volatility
n_days = 60
initial_price = 150.0
returns = np.random.normal(0.0005, 0.018, n_days)  # Reduced bias, smaller volatility
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
        gap = np.random.normal(0, close_prices[i - 1] * 0.004)
        open_prices[i] = close_prices[i - 1] + gap

    # High and low based on volatility
    volatility = abs(close_prices[i] - open_prices[i]) + np.random.uniform(0.3, 1.5)
    if close_prices[i] >= open_prices[i]:  # Bullish candle
        high_prices[i] = max(open_prices[i], close_prices[i]) + np.random.uniform(0.2, volatility)
        low_prices[i] = min(open_prices[i], close_prices[i]) - np.random.uniform(0.1, volatility * 0.6)
    else:  # Bearish candle
        high_prices[i] = max(open_prices[i], close_prices[i]) + np.random.uniform(0.1, volatility * 0.6)
        low_prices[i] = min(open_prices[i], close_prices[i]) - np.random.uniform(0.2, volatility)

    # Ensure high >= max(open, close) and low <= min(open, close)
    high_prices[i] = max(high_prices[i], open_prices[i], close_prices[i])
    low_prices[i] = min(low_prices[i], open_prices[i], close_prices[i])

    # Volume: higher on days with larger price moves
    base_volume = 5_000_000
    move_factor = 1 + abs(close_prices[i] - open_prices[i]) / open_prices[i] * 15
    volumes[i] = int(base_volume * move_factor * np.random.uniform(0.7, 1.3))

# Convert dates to JavaScript timestamps (milliseconds since epoch)
timestamps = [int(d.timestamp() * 1000) for d in dates]

# Prepare data for Highcharts
ohlc_data = []
volume_data = []

# Colorblind-friendly colors: blue for up, orange for down
UP_COLOR = "#4467A3"  # Blue (Okabe-Ito position 3)
DOWN_COLOR = "#AE3030"  # Orange (Okabe-Ito position 5)

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
    color = UP_COLOR if close_prices[i] >= open_prices[i] else DOWN_COLOR
    volume_data.append({"x": timestamps[i], "y": int(volumes[i]), "color": color})

# Convert to JSON for JavaScript
ohlc_json = json.dumps(ohlc_data)
volume_json = json.dumps(volume_data)

# Chart configuration using Highstock (for synchronized charts)
chart_js = f"""
Highcharts.stockChart('container', {{
    chart: {{
        width: 4800,
        height: 2700,
        backgroundColor: '{PAGE_BG}',
        spacingBottom: 120,
        style: {{
            fontFamily: 'Arial, sans-serif',
            color: '{INK}'
        }}
    }},

    title: {{
        text: 'candlestick-volume · highcharts · anyplot.ai',
        style: {{
            fontSize: '28px',
            fontWeight: 'bold',
            color: '{INK}'
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

    yAxis: [{{
        labels: {{
            align: 'right',
            x: -10,
            style: {{
                fontSize: '18px',
                color: '{INK_SOFT}'
            }},
            formatter: function() {{
                return '$' + this.value.toFixed(0);
            }}
        }},
        title: {{
            text: 'Price (USD)',
            style: {{
                fontSize: '22px',
                color: '{INK}'
            }}
        }},
        height: '70%',
        lineWidth: 2,
        lineColor: '{INK_SOFT}',
        resize: {{
            enabled: false
        }},
        gridLineWidth: 1,
        gridLineColor: '{GRID}'
    }}, {{
        labels: {{
            align: 'right',
            x: -10,
            style: {{
                fontSize: '18px',
                color: '{INK_SOFT}'
            }},
            formatter: function() {{
                return (this.value / 1000000).toFixed(1) + 'M';
            }}
        }},
        title: {{
            text: 'Volume',
            style: {{
                fontSize: '22px',
                color: '{INK}'
            }}
        }},
        top: '72%',
        height: '22%',
        offset: 0,
        lineWidth: 2,
        lineColor: '{INK_SOFT}',
        gridLineWidth: 1,
        gridLineColor: '{GRID}'
    }}],

    xAxis: {{
        type: 'datetime',
        labels: {{
            style: {{
                fontSize: '18px',
                color: '{INK_SOFT}'
            }},
            format: '{{value:%b %d}}',
            y: 50
        }},
        lineWidth: 2,
        lineColor: '{INK_SOFT}',
        tickColor: '{INK_SOFT}',
        gridLineWidth: 1,
        gridLineColor: '{GRID}',
        crosshair: {{
            width: 2,
            color: '{INK_SOFT}',
            snap: false
        }}
    }},

    tooltip: {{
        split: true,
        style: {{
            fontSize: '18px',
            color: '{INK}'
        }}
    }},

    legend: {{
        enabled: true,
        align: 'right',
        verticalAlign: 'top',
        layout: 'vertical',
        x: -100,
        y: 80,
        itemStyle: {{
            color: '{INK}'
        }},
        backgroundColor: '{ELEVATED_BG}',
        borderColor: '{INK_SOFT}',
        borderWidth: 1
    }},

    plotOptions: {{
        candlestick: {{
            color: '{DOWN_COLOR}',
            upColor: '{UP_COLOR}',
            lineColor: '{DOWN_COLOR}',
            upLineColor: '{UP_COLOR}',
            lineWidth: 2
        }},
        column: {{
            borderWidth: 0
        }}
    }},

    series: [{{
        type: 'candlestick',
        name: 'Stock Price',
        data: OHLC_DATA_PLACEHOLDER,
        yAxis: 0
    }}, {{
        type: 'column',
        name: 'Volume',
        data: VOLUME_DATA_PLACEHOLDER,
        yAxis: 1
    }}]
}});
"""

# Replace data placeholders
chart_js = chart_js.replace("OHLC_DATA_PLACEHOLDER", ohlc_json)
chart_js = chart_js.replace("VOLUME_DATA_PLACEHOLDER", volume_json)

# Download Highcharts and Highstock JS
highcharts_url = "https://code.highcharts.com/stock/highstock.js"
req = urllib.request.Request(highcharts_url)
req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")
except urllib.error.HTTPError as e:
    # If we get a 403, try alternative CDN
    if e.code == 403:
        print("CDN blocked (403), trying jsDelivr CDN...")
        alt_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highstock.js"
        req = urllib.request.Request(alt_url)
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
    else:
        raise

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
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

# Also save HTML for interactive version with theme suffix
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
