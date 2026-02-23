""" pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 74/100 | Updated: 2026-02-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Company market share by sector
data = [
    {
        "name": "Technology",
        "data": [
            {"name": "Software", "value": 850},
            {"name": "Hardware", "value": 420},
            {"name": "Cloud Services", "value": 680},
            {"name": "Semiconductors", "value": 390},
            {"name": "Cybersecurity", "value": 280},
        ],
    },
    {
        "name": "Finance",
        "data": [
            {"name": "Banking", "value": 720},
            {"name": "Insurance", "value": 480},
            {"name": "Asset Management", "value": 350},
            {"name": "Fintech", "value": 260},
        ],
    },
    {
        "name": "Healthcare",
        "data": [
            {"name": "Pharmaceuticals", "value": 580},
            {"name": "Medical Devices", "value": 320},
            {"name": "Biotech", "value": 420},
            {"name": "Healthcare Services", "value": 240},
        ],
    },
    {
        "name": "Energy",
        "data": [
            {"name": "Oil & Gas", "value": 550},
            {"name": "Renewables", "value": 380},
            {"name": "Utilities", "value": 290},
        ],
    },
    {
        "name": "Consumer",
        "data": [
            {"name": "Retail", "value": 460},
            {"name": "Food & Beverage", "value": 340},
            {"name": "Automotive", "value": 510},
            {"name": "Entertainment", "value": 270},
        ],
    },
]

# Colorblind-safe palette for sectors
colors = ["#306998", "#E5A02E", "#9467BD", "#17BECF", "#8C564B"]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "packedbubble",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "margin": [100, 50, 100, 50],
}

# Title
chart.options.title = {
    "text": "bubble-packed \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Market value by sector ($B)", "style": {"fontSize": "36px", "color": "#666666"}}

# Tooltip
chart.options.tooltip = {
    "useHTML": True,
    "style": {"fontSize": "28px"},
    "pointFormat": "<b>{point.name}</b>: ${point.value}B",
}

# Legend
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "36px"}, "symbolHeight": 24, "symbolWidth": 24}

# Plot options for packed bubble
chart.options.plot_options = {
    "packedbubble": {
        "minSize": "80%",
        "maxSize": "250%",
        "zMin": 0,
        "zMax": 1000,
        "layoutAlgorithm": {
            "gravitationalConstant": 0.05,
            "splitSeries": False,
            "seriesInteraction": True,
            "dragBetweenSeries": False,
            "parentNodeLimit": False,
        },
        "dataLabels": {
            "enabled": True,
            "format": "{point.name}",
            "filter": {"property": "y", "operator": ">", "value": 260},
            "style": {"fontSize": "28px", "fontWeight": "bold", "color": "white", "textOutline": "2px contrast"},
        },
    }
}

# Add series with colors
series_list = []
for i, sector in enumerate(data):
    series_list.append(
        {"type": "packedbubble", "name": sector["name"], "data": sector["data"], "color": colors[i % len(colors)]}
    )

chart.options.series = series_list

# Download Highcharts JS and highcharts-more.js for packed bubble support
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts-more.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts/highcharts-more.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(standalone_html)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
