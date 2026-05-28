""" anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: highcharts unknown | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-17
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

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
chart_js = f"""
Highcharts.chart('container', {{
    chart: {{
        width: 4800,
        height: 2700,
        backgroundColor: '{PAGE_BG}',
        marginBottom: 250,
        marginTop: 200,
        marginLeft: 200,
        marginRight: 150,
        style: {{
            fontFamily: 'Arial, sans-serif',
            color: '{INK}'
        }}
    }},

    title: {{
        text: 'indicator-bollinger · highcharts · anyplot.ai',
        style: {{
            fontSize: '28px',
            fontWeight: 'bold',
            color: '{INK}'
        }}
    }},

    credits: {{
        enabled: false
    }},

    xAxis: {{
        type: 'datetime',
        title: {{
            text: 'Date',
            style: {{
                fontSize: '22px',
                color: '{INK}'
            }},
            margin: 40
        }},
        labels: {{
            style: {{
                fontSize: '18px',
                color: '{INK_SOFT}'
            }},
            format: '{{value:%b %Y}}',
            y: 35
        }},
        tickInterval: 30 * 24 * 3600 * 1000,
        lineColor: '{INK_SOFT}',
        lineWidth: 2,
        tickColor: '{INK_SOFT}',
        tickWidth: 2,
        gridLineWidth: 1,
        gridLineColor: '{GRID}'
    }},

    yAxis: {{
        title: {{
            text: 'Price (USD)',
            style: {{
                fontSize: '22px',
                color: '{INK}'
            }},
            margin: 30
        }},
        labels: {{
            style: {{
                fontSize: '18px',
                color: '{INK_SOFT}'
            }},
            format: '${{value:.0f}}',
            x: -10
        }},
        gridLineWidth: 1,
        gridLineColor: '{GRID}',
        gridLineDashStyle: 'Dash'
    }},

    legend: {{
        enabled: true,
        layout: 'horizontal',
        align: 'center',
        verticalAlign: 'top',
        y: 100,
        itemStyle: {{
            fontSize: '18px',
            color: '{INK_SOFT}'
        }},
        backgroundColor: '{ELEVATED_BG}',
        borderColor: '{INK_SOFT}',
        borderWidth: 1,
        borderRadius: 8,
        symbolWidth: 50,
        symbolHeight: 16
    }},

    tooltip: {{
        shared: true,
        crosshairs: true,
        style: {{
            fontSize: '18px',
            color: '{INK}'
        }},
        headerFormat: '<b>{{point.x:%b %d, %Y}}</b><br/>',
        pointFormat: '<span style="color:{{point.color}}">●</span> {{series.name}}: <b>${{point.y:.2f}}</b><br/>'
    }},

    plotOptions: {{
        series: {{
            animation: false
        }},
        line: {{
            lineWidth: 5,
            marker: {{
                enabled: false
            }}
        }},
        arearange: {{
            fillOpacity: 0.25,
            lineWidth: 0,
            marker: {{
                enabled: false
            }}
        }}
    }},

    colors: {json.dumps(IMPRINT)},

    series: [{{
        type: 'arearange',
        name: 'Bollinger Bands',
        data: {band_json},
        color: '{IMPRINT[2]}',
        fillOpacity: 0.2,
        lineWidth: 0,
        zIndex: 0,
        enableMouseTracking: false
    }}, {{
        type: 'line',
        name: 'Upper Band (+2σ)',
        data: {upper_json},
        color: '{IMPRINT[2]}',
        lineWidth: 4,
        dashStyle: 'Dash',
        zIndex: 1
    }}, {{
        type: 'line',
        name: 'Lower Band (-2σ)',
        data: {lower_json},
        color: '{IMPRINT[2]}',
        lineWidth: 4,
        dashStyle: 'Dash',
        zIndex: 1
    }}, {{
        type: 'line',
        name: '20-Day SMA',
        data: {sma_json},
        color: '{IMPRINT[1]}',
        lineWidth: 5,
        dashStyle: 'Dot',
        zIndex: 2
    }}, {{
        type: 'line',
        name: 'Close Price',
        data: {close_json},
        color: '{IMPRINT[0]}',
        lineWidth: 6,
        zIndex: 3
    }}]
}});
"""

# Download Highcharts JS for inline embedding
try:
    highcharts_url = "https://code.highcharts.com/highcharts.js"
    req = urllib.request.Request(highcharts_url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")
except Exception as e:
    print(f"Warning: Could not download Highcharts JS: {e}")
    highcharts_js = "// Highcharts JS unavailable"

# Download highcharts-more for arearange series
try:
    highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
    req = urllib.request.Request(highcharts_more_url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_more_js = response.read().decode("utf-8")
except Exception as e:
    print(f"Warning: Could not download Highcharts-more JS: {e}")
    highcharts_more_js = "// Highcharts-more JS unavailable"

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    {chart_js}
    </script>
</body>
</html>"""

# Save HTML for interactive version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML file for screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Take screenshot using Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
