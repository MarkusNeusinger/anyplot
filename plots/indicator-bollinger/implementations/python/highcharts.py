""" pyplots.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2026-01-07
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Generate 120 days of stock price data with Bollinger Bands
np.random.seed(42)
n_days = 120
start_price = 150.0

# Generate realistic price movements with trend and volatility
returns = np.random.normal(0.001, 0.02, n_days)
prices = start_price * np.cumprod(1 + returns)

# Add some volatility clustering (GARCH-like effect)
volatility_factor = 1 + 0.5 * np.sin(np.linspace(0, 4 * np.pi, n_days))
prices = start_price + np.cumsum(returns * volatility_factor * start_price)
prices = np.maximum(prices, 50)  # Ensure positive prices

# Create date range
dates = pd.date_range(start="2024-01-01", periods=n_days, freq="B")

# Calculate Bollinger Bands (20-period SMA with 2 standard deviations)
window = 20
df = pd.DataFrame({"date": dates, "close": prices})
df["sma"] = df["close"].rolling(window=window).mean()
df["std"] = df["close"].rolling(window=window).std()
df["upper_band"] = df["sma"] + 2 * df["std"]
df["lower_band"] = df["sma"] - 2 * df["std"]

# Remove NaN values from rolling calculations
df = df.dropna().reset_index(drop=True)

# Convert dates to timestamps for Highcharts (milliseconds since epoch)
timestamps = [int(d.timestamp() * 1000) for d in df["date"]]

# Prepare data for Highcharts
close_data = [[timestamps[i], round(float(df["close"].iloc[i]), 2)] for i in range(len(df))]
sma_data = [[timestamps[i], round(float(df["sma"].iloc[i]), 2)] for i in range(len(df))]
upper_data = [[timestamps[i], round(float(df["upper_band"].iloc[i]), 2)] for i in range(len(df))]
lower_data = [[timestamps[i], round(float(df["lower_band"].iloc[i]), 2)] for i in range(len(df))]

# Area range data for band fill [timestamp, low, high]
band_data = [
    [timestamps[i], round(float(df["lower_band"].iloc[i]), 2), round(float(df["upper_band"].iloc[i]), 2)]
    for i in range(len(df))
]

# Convert to JSON for JavaScript
close_json = json.dumps(close_data)
sma_json = json.dumps(sma_data)
upper_json = json.dumps(upper_data)
lower_json = json.dumps(lower_data)
band_json = json.dumps(band_data)

# Chart configuration using raw JavaScript
chart_js = """
Highcharts.chart('container', {
    chart: {
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff',
        marginBottom: 250,
        marginTop: 200,
        marginLeft: 200,
        marginRight: 150,
        style: {
            fontFamily: 'Arial, sans-serif'
        }
    },

    title: {
        text: 'indicator-bollinger \\u00b7 highcharts \\u00b7 pyplots.ai',
        style: {
            fontSize: '64px',
            fontWeight: 'bold'
        }
    },

    subtitle: {
        text: '20-Day SMA with 2 Standard Deviation Bands',
        style: {
            fontSize: '36px',
            color: '#666666'
        }
    },

    credits: {
        enabled: false
    },

    xAxis: {
        type: 'datetime',
        title: {
            text: 'Date',
            style: {
                fontSize: '40px'
            },
            margin: 40
        },
        labels: {
            style: {
                fontSize: '28px'
            },
            format: '{value:%b %Y}',
            y: 35
        },
        tickInterval: 30 * 24 * 3600 * 1000,
        lineWidth: 3,
        tickWidth: 3,
        gridLineWidth: 1,
        gridLineColor: '#E5E5E5'
    },

    yAxis: {
        title: {
            text: 'Price (USD)',
            style: {
                fontSize: '40px'
            },
            margin: 30
        },
        labels: {
            style: {
                fontSize: '32px'
            },
            format: '${value:.0f}',
            x: -10
        },
        gridLineWidth: 1,
        gridLineColor: '#E5E5E5',
        gridLineDashStyle: 'Dash'
    },

    legend: {
        enabled: true,
        layout: 'horizontal',
        align: 'center',
        verticalAlign: 'top',
        y: 100,
        itemStyle: {
            fontSize: '28px'
        },
        symbolWidth: 50,
        symbolHeight: 16
    },

    tooltip: {
        shared: true,
        crosshairs: true,
        style: {
            fontSize: '24px'
        },
        headerFormat: '<b>{point.x:%b %d, %Y}</b><br/>',
        pointFormat: '<span style="color:{point.color}">\\u25cf</span> {series.name}: <b>${point.y:.2f}</b><br/>'
    },

    plotOptions: {
        series: {
            animation: false
        },
        line: {
            lineWidth: 5,
            marker: {
                enabled: false
            }
        },
        arearange: {
            fillOpacity: 0.25,
            lineWidth: 0,
            marker: {
                enabled: false
            }
        }
    },

    series: [{
        type: 'arearange',
        name: 'Bollinger Bands',
        data: BAND_DATA_PLACEHOLDER,
        color: '#306998',
        fillOpacity: 0.2,
        lineWidth: 0,
        zIndex: 0,
        enableMouseTracking: false
    }, {
        type: 'line',
        name: 'Upper Band (+2\\u03c3)',
        data: UPPER_DATA_PLACEHOLDER,
        color: '#306998',
        lineWidth: 4,
        dashStyle: 'Dash',
        zIndex: 1
    }, {
        type: 'line',
        name: 'Lower Band (-2\\u03c3)',
        data: LOWER_DATA_PLACEHOLDER,
        color: '#306998',
        lineWidth: 4,
        dashStyle: 'Dash',
        zIndex: 1
    }, {
        type: 'line',
        name: '20-Day SMA',
        data: SMA_DATA_PLACEHOLDER,
        color: '#FFD43B',
        lineWidth: 5,
        dashStyle: 'Dot',
        zIndex: 2
    }, {
        type: 'line',
        name: 'Close Price',
        data: CLOSE_DATA_PLACEHOLDER,
        color: '#17BECF',
        lineWidth: 6,
        zIndex: 3
    }]
});
"""

# Replace data placeholders
chart_js = chart_js.replace("BAND_DATA_PLACEHOLDER", band_json)
chart_js = chart_js.replace("UPPER_DATA_PLACEHOLDER", upper_json)
chart_js = chart_js.replace("LOWER_DATA_PLACEHOLDER", lower_json)
chart_js = chart_js.replace("SMA_DATA_PLACEHOLDER", sma_json)
chart_js = chart_js.replace("CLOSE_DATA_PLACEHOLDER", close_json)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download highcharts-more for arearange series
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
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
time.sleep(6)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
