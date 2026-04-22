""" pyplots.ai
scatter-brush-zoom: Interactive Scatter Plot with Brush Selection and Zoom
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Generate multi-cluster dataset for demonstrating brush selection
np.random.seed(42)

# Create 4 distinct clusters
n_per_cluster = 75
clusters = []

# Cluster 1: Lower-left (Batch A)
x1 = np.random.normal(25, 6, n_per_cluster)
y1 = np.random.normal(30, 7, n_per_cluster)
clusters.append(("Batch A", x1, y1, "#306998"))

# Cluster 2: Upper-right (Batch B)
x2 = np.random.normal(75, 8, n_per_cluster)
y2 = np.random.normal(80, 6, n_per_cluster)
clusters.append(("Batch B", x2, y2, "#FFD43B"))

# Cluster 3: Center (Batch C)
x3 = np.random.normal(50, 10, n_per_cluster)
y3 = np.random.normal(50, 10, n_per_cluster)
clusters.append(("Batch C", x3, y3, "#9467BD"))

# Cluster 4: Upper-left (Batch D)
x4 = np.random.normal(20, 5, n_per_cluster)
y4 = np.random.normal(75, 6, n_per_cluster)
clusters.append(("Batch D", x4, y4, "#17BECF"))

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration with zoom enabled (brush selection via zoomType: 'xy')
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "zoomType": "xy",  # Enable brush selection/zoom in both axes
    "panning": {"enabled": True, "type": "xy"},  # Enable panning when zoomed
    "panKey": "shift",  # Hold shift to pan
    "spacingBottom": 120,  # Extra space at bottom for X-axis label
    "resetZoomButton": {
        "position": {"align": "right", "verticalAlign": "top", "x": -60, "y": 30},
        "theme": {
            "fill": "#306998",
            "stroke": "#306998",
            "style": {"color": "#ffffff", "fontSize": "28px", "fontWeight": "bold"},
            "r": 10,
            "padding": 16,
        },
    },
    "style": {"fontFamily": "Arial, sans-serif"},
}

# Title
chart.options.title = {
    "text": "scatter-brush-zoom · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold", "color": "#333333"},
}

# Subtitle with instructions
chart.options.subtitle = {
    "text": "Click and drag to select/zoom a region • Shift+drag to pan • Click 'Reset zoom' to clear",
    "style": {"fontSize": "28px", "color": "#666666"},
}

# X-Axis
chart.options.x_axis = {
    "title": {
        "text": "Process Parameter X",
        "style": {"fontSize": "36px", "color": "#333333", "fontWeight": "bold"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#333333"}, "enabled": True},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
    "min": 0,
    "max": 100,
    "tickInterval": 10,
    "showFirstLabel": True,
    "showLastLabel": True,
}

# Y-Axis
chart.options.y_axis = {
    "title": {"text": "Process Parameter Y", "style": {"fontSize": "36px", "color": "#333333", "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "28px", "color": "#333333"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
    "min": 0,
    "max": 100,
    "tickInterval": 10,
}

# Plot options for scatter
chart.options.plot_options = {
    "scatter": {
        "marker": {
            "radius": 14,  # Larger markers for 4800x2700 canvas
            "states": {
                "hover": {"enabled": True, "lineColor": "#000000", "lineWidth": 3, "radius": 18},
                "select": {"enabled": True, "fillColor": "#ff6600", "lineColor": "#000000", "lineWidth": 4},
            },
        },
        "allowPointSelect": True,  # Enable point selection
        "states": {"inactive": {"opacity": 0.4}},
    }
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "32px", "fontWeight": "normal", "color": "#333333"},
    "itemMarginBottom": 20,
    "symbolRadius": 10,
    "symbolHeight": 24,
    "symbolWidth": 24,
}

# Tooltip
chart.options.tooltip = {
    "headerFormat": "<b>{series.name}</b><br>",
    "pointFormat": "X: {point.x:.1f}<br>Y: {point.y:.1f}",
    "style": {"fontSize": "22px"},
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#306998",
    "borderRadius": 8,
    "borderWidth": 2,
}

# Credits
chart.options.credits = {"enabled": False}

# Add series for each cluster
for name, x, y, color in clusters:
    series = ScatterSeries()
    series.data = [[float(xi), float(yi)] for xi, yi in zip(x, y, strict=False)]
    series.name = name
    series.color = color
    series.marker = {"symbol": "circle", "fillColor": color, "lineWidth": 1, "lineColor": "#ffffff"}
    chart.add_series(series)

# Download Highcharts JS for inline embedding (headless Chrome cannot load from CDN)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate JS literal for chart
html_str = chart.to_js_literal()

# Create HTML with inline Highcharts (required for headless Chrome)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Scatter Brush Zoom - Highcharts</title>
    <script>{highcharts_js}</script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }}
        #container {{
            width: 4800px;
            height: 2700px;
        }}
    </style>
</head>
<body>
    <div id="container"></div>
    <script>
        {html_str}
    </script>
</body>
</html>"""

# Save interactive HTML version
with open("plot.html", "w", encoding="utf-8") as f:
    # For standalone HTML, use CDN for smaller file
    html_standalone = (
        """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Scatter Brush Zoom - Highcharts</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
        }
        #container {
            width: 100%;
            max-width: 1600px;
            height: 900px;
            margin: 0 auto;
            background-color: #ffffff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div id="container"></div>
    <script>
        """
        + html_str
        + """
    </script>
</body>
</html>"""
    )
    f.write(html_standalone)

# Generate PNG using Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")  # Extra height for x-axis
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
