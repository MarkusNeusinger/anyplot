""" pyplots.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2026-01-19
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - 6 dashboard metrics with history and change
np.random.seed(42)

metrics = [
    {
        "name": "CPU Usage",
        "value": 45,
        "unit": "%",
        "history": (30 + np.cumsum(np.random.randn(20) * 3)).clip(20, 80).tolist(),
        "change": -5.2,
        "status": "good",
    },
    {
        "name": "Memory",
        "value": 72,
        "unit": "%",
        "history": (60 + np.cumsum(np.random.randn(20) * 2)).clip(40, 90).tolist(),
        "change": 8.3,
        "status": "warning",
    },
    {
        "name": "Response Time",
        "value": 120,
        "unit": "ms",
        "history": (150 + np.cumsum(np.random.randn(20) * 10)).clip(80, 250).tolist(),
        "change": -15.0,
        "status": "good",
    },
    {
        "name": "Requests/sec",
        "value": 1250,
        "unit": "",
        "history": (1000 + np.cumsum(np.random.randn(20) * 50)).clip(800, 1500).tolist(),
        "change": 12.5,
        "status": "good",
    },
    {
        "name": "Error Rate",
        "value": 2.3,
        "unit": "%",
        "history": (1.5 + np.cumsum(np.random.randn(20) * 0.3)).clip(0.5, 5).tolist(),
        "change": 0.8,
        "status": "warning",
    },
    {
        "name": "Disk I/O",
        "value": 156,
        "unit": "MB/s",
        "history": (120 + np.cumsum(np.random.randn(20) * 15)).clip(80, 250).tolist(),
        "change": -3.2,
        "status": "good",
    },
]

# Status colors
status_colors = {"good": "#059669", "warning": "#D97706", "critical": "#DC2626"}

# Change colors (green for down is good for CPU/Memory/Error, up is good for Requests)
# Metrics where lower is better
lower_is_better = {"CPU Usage", "Memory", "Response Time", "Error Rate"}


def get_change_color(metric_name, change):
    if metric_name in lower_is_better:
        return "#059669" if change <= 0 else "#DC2626"
    else:
        return "#059669" if change >= 0 else "#DC2626"


def get_arrow(change):
    return "▲" if change >= 0 else "▼"


# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Build HTML dashboard with 6 tiles (3x2 grid)
tile_width = 1500
tile_height = 1200
gap = 60
cols = 3
rows = 2

total_width = cols * tile_width + (cols + 1) * gap
total_height = rows * tile_height + (rows + 1) * gap + 180  # Extra for title

tiles_html = ""
tiles_js = ""

for i, m in enumerate(metrics):
    row = i // cols
    col = i % cols
    left = gap + col * (tile_width + gap)
    top = 180 + gap + row * (tile_height + gap)  # Offset for main title

    status_color = status_colors[m["status"]]
    change_color = get_change_color(m["name"], m["change"])
    arrow = get_arrow(m["change"])
    change_text = f"{arrow} {abs(m['change']):.1f}%"

    # Format value
    if m["value"] >= 1000:
        value_str = f"{m['value']:,.0f}"
    elif isinstance(m["value"], float):
        value_str = f"{m['value']:.1f}"
    else:
        value_str = str(m["value"])

    tile_id = f"tile_{i}"
    chart_id = f"chart_{i}"

    # Tile HTML
    tiles_html += f"""
    <div id="{tile_id}" style="
        position: absolute;
        left: {left}px;
        top: {top}px;
        width: {tile_width}px;
        height: {tile_height}px;
        background: #ffffff;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border-left: 8px solid {status_color};
        padding: 40px;
        box-sizing: border-box;
    ">
        <div style="font-size: 36px; color: #6B7280; font-weight: 500; margin-bottom: 15px;">
            {m["name"]}
        </div>
        <div style="display: flex; align-items: baseline; margin-bottom: 20px;">
            <span style="font-size: 96px; font-weight: 700; color: #1F2937;">
                {value_str}
            </span>
            <span style="font-size: 40px; color: #6B7280; margin-left: 10px;">
                {m["unit"]}
            </span>
        </div>
        <div style="font-size: 32px; color: {change_color}; font-weight: 600; margin-bottom: 30px;">
            {change_text}
        </div>
        <div id="{chart_id}" style="width: 100%; height: 400px;"></div>
    </div>
    """

    # Sparkline chart JS
    sparkline_data = m["history"]
    spark_color = "#306998"  # Python blue

    tiles_js += f"""
    Highcharts.chart('{chart_id}', {{
        chart: {{
            type: 'area',
            backgroundColor: 'transparent',
            margin: [0, 0, 0, 0],
            spacing: [0, 0, 0, 0]
        }},
        title: {{ text: null }},
        credits: {{ enabled: false }},
        xAxis: {{
            visible: false
        }},
        yAxis: {{
            visible: false
        }},
        legend: {{ enabled: false }},
        tooltip: {{ enabled: false }},
        plotOptions: {{
            area: {{
                fillColor: {{
                    linearGradient: {{ x1: 0, y1: 0, x2: 0, y2: 1 }},
                    stops: [
                        [0, '{spark_color}40'],
                        [1, '{spark_color}10']
                    ]
                }},
                lineWidth: 4,
                color: '{spark_color}',
                marker: {{ enabled: false }},
                states: {{ hover: {{ enabled: false }} }}
            }}
        }},
        series: [{{
            data: {sparkline_data}
        }}]
    }});
    """

# Main title
title_html = f"""
<div style="
    position: absolute;
    left: 0;
    top: 40px;
    width: {total_width}px;
    text-align: center;
    font-size: 56px;
    font-weight: 700;
    color: #1F2937;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
">
    dashboard-metrics-tiles · highcharts · pyplots.ai
</div>
"""

# Full HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        * {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
    </style>
</head>
<body style="margin: 0; background: #F3F4F6;">
    <div style="position: relative; width: {total_width}px; height: {total_height}px;">
        {title_html}
        {tiles_html}
    </div>
    <script>
        {tiles_js}
    </script>
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument(f"--window-size={total_width},{total_height}")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
