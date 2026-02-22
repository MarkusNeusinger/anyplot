""" pyplots.ai
bullet-basic: Basic Bullet Chart
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 87/100 | Updated: 2026-02-22
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Q4 KPI dashboard with actual values, targets, and qualitative ranges
metrics = [
    {"name": "Revenue", "actual": 275, "target": 250, "max": 300, "label": "$275K"},
    {"name": "Profit", "actual": 22, "target": 27, "max": 35, "label": "22%"},
    {"name": "New Customers", "actual": 1650, "target": 1500, "max": 2000, "label": "1,650"},
    {"name": "Satisfaction", "actual": 4.5, "target": 4.7, "max": 5.0, "label": "4.5/5"},
]

# Qualitative range thresholds as percentage of max — poor / satisfactory / good
range_pcts = [50, 75, 100]

# Grayscale for qualitative ranges — light to dark = poor to good
range_colors = ["#e0e0e0", "#b0b0b0", "#808080"]

# Normalize all values to 0-100% scale for a shared axis
series_data = []
for m in metrics:
    series_data.append(
        {
            "y": round(m["actual"] / m["max"] * 100, 1),
            "target": round(m["target"] / m["max"] * 100, 1),
            "label": m["label"],
        }
    )

categories = [m["name"] for m in metrics]

# Chart configuration
chart_options = {
    "chart": {
        "type": "bullet",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "inverted": True,
        "marginLeft": 380,
        "marginRight": 100,
        "spacing": [80, 60, 60, 60],
    },
    "title": {
        "text": "Q4 Performance Dashboard \u00b7 bullet-basic \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "bold"},
    },
    "subtitle": {
        "text": "Actual performance vs targets across key business metrics",
        "style": {"fontSize": "30px", "color": "#666666"},
    },
    "xAxis": {"categories": categories, "labels": {"style": {"fontSize": "32px", "fontWeight": "bold"}}},
    "yAxis": {
        "gridLineWidth": 0,
        "min": 0,
        "max": 100,
        "title": {"text": "% of Maximum", "style": {"fontSize": "28px"}},
        "tickInterval": 10,
        "labels": {"format": "{value}%", "style": {"fontSize": "24px"}},
        "plotBands": [
            {"from": 0, "to": range_pcts[0], "color": range_colors[0]},
            {"from": range_pcts[0], "to": range_pcts[1], "color": range_colors[1]},
            {"from": range_pcts[1], "to": range_pcts[2], "color": range_colors[2]},
        ],
    },
    "legend": {"enabled": False},
    "plotOptions": {
        "bullet": {
            "pointPadding": 0.15,
            "borderWidth": 0,
            "groupPadding": 0.05,
            "color": "#306998",
            "targetOptions": {"width": "180%", "height": 6, "borderWidth": 0, "color": "#1a1a1a"},
            "dataLabels": {
                "enabled": True,
                "format": "{point.label}",
                "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#ffffff"},
                "inside": True,
                "align": "right",
            },
        }
    },
    "series": [{"name": "Performance", "data": series_data}],
    "tooltip": {
        "headerFormat": '<span style="font-size: 24px; font-weight: bold;">{point.key}</span><br/>',
        "pointFormat": (
            '<span style="font-size: 20px;">'
            "Actual: <b>{point.label}</b> ({point.y}%)<br/>"
            "Target: {point.target}%"
            "</span>"
        ),
    },
    "credits": {"enabled": False},
}

# Download Highcharts JS files for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
bullet_url = "https://code.highcharts.com/modules/bullet.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

with urllib.request.urlopen(bullet_url, timeout=30) as response:
    bullet_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
chart_options_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{bullet_js}</script>
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

# Save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
