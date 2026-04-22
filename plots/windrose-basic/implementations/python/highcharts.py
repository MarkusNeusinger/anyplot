""" pyplots.ai
windrose-basic: Wind Rose Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Simulated hourly wind measurements (8760 observations, one year)
np.random.seed(42)
n_obs = 8760

# Create wind directions with prevailing westerly pattern
direction_base = np.concatenate(
    [
        np.random.normal(270, 40, int(n_obs * 0.35)),  # Westerly dominant
        np.random.normal(225, 30, int(n_obs * 0.20)),  # Southwest secondary
        np.random.normal(180, 50, int(n_obs * 0.15)),  # South
        np.random.normal(315, 35, int(n_obs * 0.15)),  # Northwest
        np.random.uniform(0, 360, int(n_obs * 0.15)),  # Random
    ]
)
directions = direction_base[:n_obs] % 360

# Create wind speeds with Weibull-like distribution
speeds = np.random.weibull(2, n_obs) * 6

# Define direction bins (8 sectors)
dir_bins = np.arange(0, 361, 45)
dir_labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Define speed bins (m/s)
speed_bins = [0, 3, 6, 9, 12, np.inf]
speed_labels = ["0-3", "3-6", "6-9", "9-12", ">12"]

# Adjust directions for binning (shift so N is centered at 0)
dir_shifted = (directions + 22.5) % 360
dir_indices = np.digitize(dir_shifted, dir_bins) - 1
dir_indices = np.clip(dir_indices, 0, 7)

# Calculate frequencies for each direction/speed combination
speed_indices = np.digitize(speeds, speed_bins[:-1]) - 1
speed_indices = np.clip(speed_indices, 0, len(speed_labels) - 1)

freq_matrix = np.zeros((8, len(speed_labels)))
for d_idx in range(8):
    for s_idx in range(len(speed_labels)):
        mask = (dir_indices == d_idx) & (speed_indices == s_idx)
        freq_matrix[d_idx, s_idx] = np.sum(mask)

# Convert to percentages
total_obs = len(directions)
freq_pct = (freq_matrix / total_obs) * 100

# Colors - colorblind-safe progression from cool to warm
colors = ["#306998", "#4A90A4", "#FFD43B", "#FF9500", "#E74C3C"]

# Build Highcharts series data for windbarb/column polar chart
series_data = []
for s_idx, (speed_label, color) in enumerate(zip(speed_labels, colors, strict=True)):
    data_points = []
    for d_idx, dir_label in enumerate(dir_labels):
        data_points.append({"name": dir_label, "y": round(freq_pct[d_idx, s_idx], 2)})
    series_data.append({"name": f"{speed_label} m/s", "data": data_points, "color": color})

# Build the Highcharts configuration manually for polar chart
chart_config = {
    "chart": {
        "polar": True,
        "type": "column",
        "width": 3600,
        "height": 3600,
        "backgroundColor": "#ffffff",
        "marginTop": 220,
        "marginBottom": 100,
        "marginRight": 450,
    },
    "title": {
        "text": "windrose-basic · highcharts · pyplots.ai",
        "style": {"fontSize": "96px", "fontWeight": "bold"},
        "y": 80,
    },
    "subtitle": {"text": "Annual Wind Pattern Distribution", "style": {"fontSize": "60px"}, "y": 160},
    "pane": {"size": "65%", "center": ["42%", "54%"]},
    "legend": {
        "align": "right",
        "verticalAlign": "middle",
        "layout": "vertical",
        "x": -80,
        "itemStyle": {"fontSize": "54px"},
        "itemMarginBottom": 20,
        "symbolRadius": 6,
        "symbolHeight": 36,
        "symbolWidth": 36,
        "title": {"text": "Wind Speed", "style": {"fontSize": "60px", "fontWeight": "bold"}},
    },
    "xAxis": {
        "tickmarkPlacement": "on",
        "categories": dir_labels,
        "labels": {"style": {"fontSize": "60px", "fontWeight": "bold"}, "distance": 40},
    },
    "yAxis": {
        "min": 0,
        "endOnTick": False,
        "showLastLabel": True,
        "title": {"text": "Frequency (%)", "style": {"fontSize": "48px"}},
        "labels": {"style": {"fontSize": "40px"}, "format": "{value}%"},
        "reversedStacks": False,
        "gridLineWidth": 2,
        "gridLineColor": "#e0e0e0",
    },
    "tooltip": {"valueSuffix": "%", "style": {"fontSize": "40px"}},
    "plotOptions": {
        "series": {
            "stacking": "normal",
            "shadow": False,
            "groupPadding": 0,
            "pointPlacement": "on",
            "borderWidth": 2,
            "borderColor": "#ffffff",
        }
    },
    "series": series_data,
}

# Convert config to JavaScript
chart_js = json.dumps(chart_config)

# Download Highcharts JS and Highcharts More (for polar charts)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background-color:#ffffff;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>
        Highcharts.chart('container', {chart_js});
    </script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save plot.html for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    # For the standalone HTML, use CDN links
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
</head>
<body style="margin:0; background-color:#ffffff;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        Highcharts.chart('container', {chart_js});
    </script>
</body>
</html>"""
    f.write(standalone_html)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
