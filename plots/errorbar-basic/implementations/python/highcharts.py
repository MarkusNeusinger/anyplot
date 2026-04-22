""" pyplots.ai
errorbar-basic: Basic Error Bar Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Experimental measurements with error bars
categories = ["Sample A", "Sample B", "Sample C", "Sample D", "Sample E", "Sample F"]
values = [45.2, 38.7, 52.1, 41.5, 48.3, 35.9]
errors = [4.5, 3.2, 5.8, 3.9, 4.1, 2.8]

# Prepare errorbar data as [low, high] ranges
errorbar_data = [[val - err, val + err] for val, err in zip(values, errors, strict=True)]

# Chart options - using errorbar series type for proper caps
chart_options = {
    "chart": {
        "type": "column",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginBottom": 180,
        "style": {"fontFamily": "Arial, sans-serif"},
    },
    "title": {"text": "errorbar-basic · highcharts · pyplots.ai", "style": {"fontSize": "64px", "fontWeight": "bold"}},
    "subtitle": {
        "text": "Experimental measurements with error ranges",
        "style": {"fontSize": "38px", "color": "#666666"},
    },
    "xAxis": {
        "categories": categories,
        "title": {"text": "Experimental Samples", "style": {"fontSize": "42px"}},
        "labels": {"style": {"fontSize": "32px"}},
    },
    "yAxis": {
        "title": {"text": "Measured Value", "style": {"fontSize": "42px"}},
        "labels": {"style": {"fontSize": "32px"}},
        "gridLineColor": "#e0e0e0",
        "gridLineDashStyle": "Dash",
        "min": 25,
    },
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "x": -50,
        "y": 100,
        "itemStyle": {"fontSize": "32px"},
    },
    "plotOptions": {
        "column": {"pointWidth": 80, "borderWidth": 0},
        "errorbar": {"lineWidth": 6, "whiskerLength": "60%", "whiskerWidth": 6, "stemWidth": 6},
    },
    "series": [
        {"name": "Mean Value", "type": "column", "data": values, "color": "#306998"},
        {
            "name": "Error Range",
            "type": "errorbar",
            "data": errorbar_data,
            "color": "#1a1a1a",
            "stemColor": "#1a1a1a",
            "whiskerColor": "#1a1a1a",
        },
    ],
}

# Download Highcharts JS and highcharts-more (needed for errorbar)
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
chart_options_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)

# Set window size large enough to contain full chart
driver.set_window_size(4900, 2900)

driver.get(f"file://{temp_path}")
time.sleep(5)

# Take screenshot
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop/resize to exact 4800x2700 using PIL
img = Image.open("plot_raw.png")
# Create a new image with exact dimensions and white background
final_img = Image.new("RGB", (4800, 2700), (255, 255, 255))
# Paste the screenshot (crop if larger, or center if smaller)
final_img.paste(img.crop((0, 0, min(img.width, 4800), min(img.height, 2700))), (0, 0))
final_img.save("plot.png")

# Clean up raw screenshot
Path("plot_raw.png").unlink()

# Clean up temp file
Path(temp_path).unlink()
