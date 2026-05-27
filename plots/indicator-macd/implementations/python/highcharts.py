""" anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: highcharts unknown | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-16
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette for lines
MACD_COLOR = "#009E73"  # Position 1 - brand
SIGNAL_COLOR = "#BD8233"  # imprint ochre — signal line (categorical contrast)
HISTOGRAM_POS_COLOR = "#22C55E"  # Green for positive histogram
HISTOGRAM_NEG_COLOR = "#EF4444"  # Red for negative histogram

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
    color = HISTOGRAM_POS_COLOR if val >= 0 else HISTOGRAM_NEG_COLOR
    histogram_data.append({"x": timestamps[i], "y": val, "color": color})

# Convert to JSON for JavaScript
macd_json = json.dumps(macd_data)
signal_json = json.dumps(signal_data)
histogram_json = json.dumps(histogram_data)

# Chart configuration
chart_js = (
    """
Highcharts.chart('container', {
    chart: {
        width: 4800,
        height: 2700,
        backgroundColor: '"""
    + PAGE_BG
    + """',
        marginBottom: 250,
        marginTop: 200,
        marginLeft: 180,
        style: {
            fontFamily: 'Arial, sans-serif'
        }
    },

    title: {
        text: 'indicator-macd \\u00b7 highcharts \\u00b7 anyplot.ai',
        style: {
            fontSize: '28px',
            fontWeight: 'normal',
            color: '"""
    + INK
    + """'
        }
    },

    subtitle: {
        text: 'MACD (12, 26, 9) - Simulated Stock Data',
        style: {
            fontSize: '22px',
            color: '"""
    + INK_SOFT
    + """'
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
                fontSize: '22px',
                color: '"""
    + INK
    + """'
            },
            margin: 20
        },
        labels: {
            style: {
                fontSize: '18px',
                color: '"""
    + INK_SOFT
    + """'
            },
            format: '{value:%b %d}',
            y: 35,
            step: 10
        },
        tickInterval: 7 * 24 * 3600 * 1000,
        lineColor: '"""
    + INK_SOFT
    + """',
        tickColor: '"""
    + INK_SOFT
    + """',
        gridLineColor: '"""
    + GRID
    + """',
        gridLineWidth: 1
    },

    yAxis: {
        title: {
            text: 'MACD Value',
            style: {
                fontSize: '22px',
                color: '"""
    + INK
    + """'
            },
            margin: 20
        },
        labels: {
            style: {
                fontSize: '18px',
                color: '"""
    + INK_SOFT
    + """'
            },
            format: '{value:.2f}',
            x: -10
        },
        plotLines: [{
            value: 0,
            color: '"""
    + INK_SOFT
    + """',
            width: 2,
            dashStyle: 'Solid',
            zIndex: 5,
            label: {
                text: 'Zero Line',
                style: {
                    fontSize: '16px',
                    color: '"""
    + INK_SOFT
    + """'
                },
                align: 'right',
                x: -10
            }
        }],
        gridLineColor: '"""
    + GRID
    + """',
        gridLineWidth: 1,
        gridLineDashStyle: 'Dash',
        lineColor: '"""
    + INK_SOFT
    + """',
        tickColor: '"""
    + INK_SOFT
    + """'
    },

    legend: {
        enabled: true,
        layout: 'horizontal',
        align: 'center',
        verticalAlign: 'top',
        y: 80,
        itemStyle: {
            fontSize: '18px',
            color: '"""
    + INK_SOFT
    + """'
        },
        backgroundColor: '"""
    + ELEVATED_BG
    + """',
        borderColor: '"""
    + INK_SOFT
    + """',
        borderWidth: 1,
        symbolWidth: 40,
        symbolHeight: 16
    },

    tooltip: {
        shared: true,
        style: {
            fontSize: '16px',
            color: '"""
    + INK
    + """'
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
            lineWidth: 3,
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
        color: '"""
    + MACD_COLOR
    + """'
    }, {
        type: 'line',
        name: 'Signal Line',
        data: SIGNAL_DATA_PLACEHOLDER,
        color: '"""
    + SIGNAL_COLOR
    + """',
        dashStyle: 'ShortDash'
    }]
});
"""
)

# Replace data placeholders
chart_js = chart_js.replace("HISTOGRAM_DATA_PLACEHOLDER", histogram_json)
chart_js = chart_js.replace("MACD_DATA_PLACEHOLDER", macd_json)
chart_js = chart_js.replace("SIGNAL_DATA_PLACEHOLDER", signal_json)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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

# Save HTML output with theme suffix
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
