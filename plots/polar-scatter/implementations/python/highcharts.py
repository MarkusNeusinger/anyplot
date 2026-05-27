""" anyplot.ai
polar-scatter: Polar Scatter Plot
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-09
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Wind measurements with prevailing directions
np.random.seed(42)
n_points = 120

# Generate wind data with realistic prevailing directions
prevailing_angles = [45, 225, 270]
angles = []
speeds = []
categories = []

for i in range(n_points):
    base_angle = np.random.choice(prevailing_angles + [np.random.uniform(0, 360)])
    angle = (base_angle + np.random.normal(0, 30)) % 360

    if base_angle in prevailing_angles:
        speed = np.random.gamma(4, 3)
    else:
        speed = np.random.gamma(2, 2)

    if i < 40:
        category = "Morning"
    elif i < 80:
        category = "Afternoon"
    else:
        category = "Evening"

    angles.append(angle)
    speeds.append(min(speed, 25))
    categories.append(category)

angles = np.array(angles)
speeds = np.array(speeds)

# Colors for categories using Okabe-Ito palette
colors = {
    "Morning": IMPRINT[0],  # #009E73
    "Afternoon": IMPRINT[1],  # #C475FD
    "Evening": IMPRINT[2],  # #4467A3
}

# Build series data for each category
series_data = []
for category in ["Morning", "Afternoon", "Evening"]:
    mask = np.array(categories) == category
    cat_angles = angles[mask]
    cat_speeds = speeds[mask]

    data_points = [{"x": float(a), "y": float(s)} for a, s in zip(cat_angles, cat_speeds, strict=True)]
    series_data.append(
        {
            "name": category,
            "type": "scatter",
            "data": data_points,
            "color": colors[category],
            "marker": {"radius": 18, "symbol": "circle"},
        }
    )

# Build Highcharts configuration
chart_config = {
    "chart": {
        "polar": True,
        "width": 3600,
        "height": 3600,
        "backgroundColor": PAGE_BG,
        "marginTop": 140,
        "marginBottom": 120,
    },
    "title": {
        "text": "polar-scatter · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
        "y": 60,
    },
    "subtitle": {
        "text": "Wind Direction and Speed Distribution",
        "style": {"fontSize": "22px", "color": INK_SOFT},
        "y": 110,
    },
    "pane": {"size": "75%", "center": ["50%", "52%"], "startAngle": 0, "endAngle": 360},
    "xAxis": {
        "tickInterval": 45,
        "min": 0,
        "max": 360,
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "distance": 30},
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "tickPositions": [0, 45, 90, 135, 180, 225, 270, 315],
    },
    "yAxis": {
        "min": 0,
        "max": 28,
        "tickInterval": 7,
        "labels": {"format": "{value} m/s", "style": {"fontSize": "18px", "color": INK_SOFT}},
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "title": None,
    },
    "plotOptions": {
        "scatter": {"marker": {"radius": 18, "states": {"hover": {"enabled": True, "lineWidth": 2}}}},
        "series": {"animation": False},
    },
    "legend": {
        "enabled": True,
        "layout": "horizontal",
        "align": "center",
        "verticalAlign": "bottom",
        "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
        "symbolHeight": 24,
        "symbolWidth": 24,
        "y": 30,
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
    },
    "credits": {"enabled": False},
    "series": series_data,
}

# Convert config to JavaScript
chart_js = json.dumps(chart_config)

# Download Highcharts JS and highcharts-more.js for polar charts
req = urllib.request.Request(
    "https://code.highcharts.com/highcharts.js",
    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"},
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req_more = urllib.request.Request(
    "https://code.highcharts.com/highcharts-more.js",
    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"},
)
with urllib.request.urlopen(req_more, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Build custom JavaScript with formatter function
chart_script = f"""
var config = {chart_js};
// Add formatter function for compass directions
config.xAxis.labels.formatter = function() {{
    var dirs = {{0: 'N', 45: 'NE', 90: 'E', 135: 'SE', 180: 'S', 225: 'SW', 270: 'W', 315: 'NW'}};
    return dirs[this.value] || this.value + '°';
}};
Highcharts.chart('container', config);
"""

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>
        {chart_script}
    </script>
</body>
</html>"""

# Write interactive HTML file with theme suffix
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML for screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Selenium screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3800,3800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Take screenshot of just the chart container element
container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
