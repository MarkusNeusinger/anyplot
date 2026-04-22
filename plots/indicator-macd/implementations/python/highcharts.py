""" pyplots.ai
indicator-macd: MACD Technical Indicator Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
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


# Data - Generate realistic MACD data from simulated price series
np.random.seed(42)
n_days = 150  # Total days including warmup period
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")  # Business days

# Simulate realistic stock price with trend and volatility
price_returns = np.random.normal(0.001, 0.02, n_days)
price = 100 * np.cumprod(1 + price_returns)

# Calculate EMAs for MACD (12, 26, 9 parameters)
df = pd.DataFrame({"date": dates, "close": price})
df["ema12"] = df["close"].ewm(span=12, adjust=False).mean()
df["ema26"] = df["close"].ewm(span=26, adjust=False).mean()
df["macd"] = df["ema12"] - df["ema26"]
df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
df["histogram"] = df["macd"] - df["signal"]

# Use data after warmup period (after EMA converges)
df = df.iloc[35:].reset_index(drop=True)  # ~115 data points

# Convert dates to JavaScript timestamps (milliseconds since epoch)
timestamps = [int(d.timestamp() * 1000) for d in df["date"]]

# Prepare data for Highcharts
macd_data = [[timestamps[i], round(float(df["macd"].iloc[i]), 4)] for i in range(len(df))]
signal_data = [[timestamps[i], round(float(df["signal"].iloc[i]), 4)] for i in range(len(df))]

# Histogram data with colors (green for positive, red for negative)
histogram_data = []
for i in range(len(df)):
    val = round(float(df["histogram"].iloc[i]), 4)
    color = "#22C55E" if val >= 0 else "#EF4444"  # Green/Red
    histogram_data.append({"x": timestamps[i], "y": val, "color": color})

# Convert to JSON for JavaScript
macd_json = json.dumps(macd_data)
signal_json = json.dumps(signal_data)
histogram_json = json.dumps(histogram_data)

# Chart configuration
chart_js = """
Highcharts.chart('container', {
    chart: {
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff',
        marginBottom: 250,
        marginTop: 200,
        marginLeft: 180,
        style: {
            fontFamily: 'Arial, sans-serif'
        }
    },

    title: {
        text: 'indicator-macd \\u00b7 highcharts \\u00b7 pyplots.ai',
        style: {
            fontSize: '64px',
            fontWeight: 'bold'
        }
    },

    subtitle: {
        text: 'MACD (12, 26, 9) - Simulated Stock Data',
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
            format: '{value:%b %d}',
            y: 35,
            step: 10
        },
        tickInterval: 7 * 24 * 3600 * 1000,
        lineWidth: 3,
        tickWidth: 3,
        gridLineWidth: 1,
        gridLineColor: '#E5E5E5'
    },

    yAxis: {
        title: {
            text: 'MACD Value',
            style: {
                fontSize: '40px'
            },
            margin: 30
        },
        labels: {
            style: {
                fontSize: '32px'
            },
            format: '{value:.2f}',
            x: -10
        },
        plotLines: [{
            value: 0,
            color: '#333333',
            width: 4,
            dashStyle: 'Solid',
            zIndex: 5,
            label: {
                text: 'Zero Line',
                style: {
                    fontSize: '24px',
                    color: '#333333'
                },
                align: 'right',
                x: -10
            }
        }],
        gridLineWidth: 1,
        gridLineColor: '#E5E5E5',
        gridLineDashStyle: 'Dash'
    },

    legend: {
        enabled: true,
        layout: 'horizontal',
        align: 'center',
        verticalAlign: 'top',
        y: 80,
        itemStyle: {
            fontSize: '32px'
        },
        symbolWidth: 50,
        symbolHeight: 20
    },

    tooltip: {
        shared: true,
        style: {
            fontSize: '24px'
        },
        headerFormat: '<b>{point.x:%b %d, %Y}</b><br/>',
        pointFormat: '<span style="color:{point.color}">\\u25cf</span> {series.name}: <b>{point.y:.4f}</b><br/>'
    },

    plotOptions: {
        column: {
            pointPadding: 0,
            groupPadding: 0.05,
            borderWidth: 0
        },
        line: {
            lineWidth: 6,
            marker: {
                enabled: false
            }
        }
    },

    series: [{
        type: 'column',
        name: 'Histogram',
        data: HISTOGRAM_DATA_PLACEHOLDER,
        color: '#22C55E'
    }, {
        type: 'line',
        name: 'MACD Line',
        data: MACD_DATA_PLACEHOLDER,
        color: '#306998'
    }, {
        type: 'line',
        name: 'Signal Line',
        data: SIGNAL_DATA_PLACEHOLDER,
        color: '#FFD43B',
        dashStyle: 'ShortDash'
    }]
});
"""

# Replace data placeholders
chart_js = chart_js.replace("HISTOGRAM_DATA_PLACEHOLDER", histogram_json)
chart_js = chart_js.replace("MACD_DATA_PLACEHOLDER", macd_json)
chart_js = chart_js.replace("SIGNAL_DATA_PLACEHOLDER", signal_json)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
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
time.sleep(6)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
