""" pyplots.ai
polar-scatter: Polar Scatter Plot
Library: highcharts unknown | Python 3.13.11
Quality: 95/100 | Created: 2025-12-26
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Wind measurements with prevailing directions
np.random.seed(42)
n_points = 120

# Generate wind data with realistic prevailing directions
# Cluster around NE (45°), SW (225°), and W (270°) with some spread
prevailing_angles = [45, 225, 270]
angles = []
speeds = []
categories = []

for i in range(n_points):
    # Select a prevailing direction with some probability
    base_angle = np.random.choice(prevailing_angles + [np.random.uniform(0, 360)])
    angle = (base_angle + np.random.normal(0, 30)) % 360

    # Wind speed - higher for prevailing directions
    if base_angle in prevailing_angles:
        speed = np.random.gamma(4, 3)  # Stronger winds
    else:
        speed = np.random.gamma(2, 2)  # Lighter winds

    # Categorize by time of day
    if i < 40:
        category = "Morning"
    elif i < 80:
        category = "Afternoon"
    else:
        category = "Evening"

    angles.append(angle)
    speeds.append(min(speed, 25))  # Cap at 25 m/s
    categories.append(category)

angles = np.array(angles)
speeds = np.array(speeds)

# Colors for categories
colors = {
    "Morning": "#306998",  # Python Blue
    "Afternoon": "#FFD43B",  # Python Yellow
    "Evening": "#9467BD",  # Purple
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
            "marker": {"radius": 14, "symbol": "circle"},
        }
    )

# Build Highcharts configuration
chart_config = {
    "chart": {
        "polar": True,
        "width": 3600,
        "height": 3600,
        "backgroundColor": "#ffffff",
        "marginTop": 140,
        "marginBottom": 120,
    },
    "title": {
        "text": "polar-scatter \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "72px", "fontWeight": "bold"},
        "y": 60,
    },
    "subtitle": {"text": "Wind Direction and Speed Distribution", "style": {"fontSize": "48px"}, "y": 110},
    "pane": {"size": "75%", "center": ["50%", "52%"], "startAngle": 0, "endAngle": 360},
    "xAxis": {
        "tickInterval": 45,
        "min": 0,
        "max": 360,
        "labels": {"style": {"fontSize": "36px"}, "distance": 30},
        "gridLineWidth": 2,
        "gridLineColor": "rgba(0, 0, 0, 0.15)",
        "tickPositions": [0, 45, 90, 135, 180, 225, 270, 315],
    },
    "yAxis": {
        "min": 0,
        "max": 28,
        "tickInterval": 7,
        "labels": {"format": "{value} m/s", "style": {"fontSize": "28px"}},
        "gridLineWidth": 2,
        "gridLineColor": "rgba(0, 0, 0, 0.15)",
        "title": None,
    },
    "plotOptions": {
        "scatter": {"marker": {"radius": 14, "states": {"hover": {"enabled": True, "lineWidth": 2}}}},
        "series": {"animation": False},
    },
    "legend": {
        "enabled": True,
        "layout": "horizontal",
        "align": "center",
        "verticalAlign": "bottom",
        "itemStyle": {"fontSize": "36px"},
        "symbolHeight": 24,
        "symbolWidth": 24,
        "y": 30,
    },
    "credits": {"enabled": False},
    "series": series_data,
}

# Convert config to JavaScript - will need to add the formatter function separately
chart_js = json.dumps(chart_config)

# Download Highcharts JS and highcharts-more.js for polar charts
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
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
<body style="margin:0; background:#ffffff;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>
        {chart_script}
    </script>
</body>
</html>"""

# Write temp HTML for screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive HTML file
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
</head>
<body style="margin:0; background:#ffffff;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        {chart_script}
    </script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

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
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
