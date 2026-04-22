""" pyplots.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Tech companies with market metrics
np.random.seed(42)
companies = [
    "TechCorp",
    "DataFlow",
    "CloudNet",
    "ByteWorks",
    "NeuralSys",
    "QuantumIO",
    "CyberEdge",
    "AlphaCore",
    "OmniSoft",
    "GridLogic",
    "NovaCode",
    "SyncLabs",
    "PrimeData",
    "VectorAI",
    "CoreStack",
]
revenue = np.random.uniform(50, 500, 15)  # Revenue in millions
growth = revenue * 0.12 + np.random.normal(0, 15, 15)  # Growth rate %

# Create data points with names (labels)
data_points = [
    {"x": round(float(revenue[i]), 1), "y": round(float(growth[i]), 1), "name": companies[i]}
    for i in range(len(companies))
]

# Build Highcharts configuration
chart_config = {
    "chart": {
        "type": "scatter",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginBottom": 280,
        "marginTop": 120,
        "marginLeft": 220,
        "marginRight": 200,
    },
    "title": {
        "text": "scatter-annotated · highcharts · pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "bold"},
    },
    "xAxis": {
        "title": {
            "text": "Annual Revenue ($ millions)",
            "style": {"fontSize": "36px", "color": "#333333"},
            "margin": 30,
        },
        "labels": {"style": {"fontSize": "28px"}, "y": 40},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.15)",
        "min": 0,
        "max": 550,
        "tickInterval": 100,
    },
    "yAxis": {
        "title": {"text": "Year-over-Year Growth (%)", "style": {"fontSize": "36px", "color": "#333333"}, "margin": 20},
        "labels": {"style": {"fontSize": "28px"}},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.15)",
    },
    "legend": {"enabled": False},
    "credits": {"enabled": False},
    "plotOptions": {
        "scatter": {
            "marker": {"radius": 20, "fillColor": "rgba(48, 105, 152, 0.7)"},
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "style": {"fontSize": "26px", "fontWeight": "500", "textOutline": "3px white", "color": "#333333"},
                "y": -30,
                "allowOverlap": False,
            },
        }
    },
    "series": [{"type": "scatter", "name": "Companies", "color": "#306998", "data": data_points}],
}

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
chart_json = json.dumps(chart_config)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {chart_json});
        }});
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Setup headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

# Take screenshot
driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

# Cleanup
Path(temp_path).unlink()
