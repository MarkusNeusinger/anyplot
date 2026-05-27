""" anyplot.ai
scatter-brush-zoom: Interactive Scatter Plot with Brush Selection and Zoom
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-16
"""

import os
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series is always position 1)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Generate multi-cluster dataset for demonstrating brush selection
np.random.seed(42)

# Create 4 distinct clusters
n_per_cluster = 75
clusters = []

# Cluster 1: Lower-left (Batch A) - Okabe-Ito position 1 (brand green)
x1 = np.random.normal(25, 6, n_per_cluster)
y1 = np.random.normal(30, 7, n_per_cluster)
clusters.append(("Batch A", x1, y1, IMPRINT[0]))

# Cluster 2: Upper-right (Batch B) - Okabe-Ito position 2 (vermillion)
x2 = np.random.normal(75, 8, n_per_cluster)
y2 = np.random.normal(80, 6, n_per_cluster)
clusters.append(("Batch B", x2, y2, IMPRINT[1]))

# Cluster 3: Center (Batch C) - Okabe-Ito position 3 (blue)
x3 = np.random.normal(50, 10, n_per_cluster)
y3 = np.random.normal(50, 10, n_per_cluster)
clusters.append(("Batch C", x3, y3, IMPRINT[2]))

# Cluster 4: Upper-left (Batch D) - Okabe-Ito position 4 (reddish purple)
x4 = np.random.normal(20, 5, n_per_cluster)
y4 = np.random.normal(75, 6, n_per_cluster)
clusters.append(("Batch D", x4, y4, IMPRINT[3]))

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration with zoom enabled (brush selection via zoomType: 'xy')
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "zoomType": "xy",
    "panning": {"enabled": True, "type": "xy"},
    "panKey": "shift",
    "spacingBottom": 140,
    "resetZoomButton": {
        "position": {"align": "right", "verticalAlign": "top", "x": -60, "y": 30},
        "theme": {
            "fill": IMPRINT[0],
            "stroke": IMPRINT[0],
            "style": {"color": PAGE_BG, "fontSize": "22px", "fontWeight": "bold"},
            "r": 10,
            "padding": 16,
        },
    },
    "style": {"fontFamily": "Arial, sans-serif"},
}

# Title
chart.options.title = {
    "text": "scatter-brush-zoom · highcharts · anyplot.ai",
    "style": {"fontSize": "32px", "fontWeight": "bold", "color": INK},
}

# Subtitle with instructions
chart.options.subtitle = {
    "text": "Click and drag to select/zoom • Shift+drag to pan • Click 'Reset zoom' to clear",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-Axis
chart.options.x_axis = {
    "title": {
        "text": "Process Parameter X (units)",
        "style": {"fontSize": "24px", "color": INK, "fontWeight": "bold"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "20px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "min": 0,
    "max": 100,
    "tickInterval": 10,
}

# Y-Axis
chart.options.y_axis = {
    "title": {"text": "Process Parameter Y (units)", "style": {"fontSize": "24px", "color": INK, "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "20px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "min": 0,
    "max": 100,
    "tickInterval": 10,
}

# Plot options for scatter
chart.options.plot_options = {
    "scatter": {
        "marker": {
            "radius": 12,
            "states": {
                "hover": {"enabled": True, "lineColor": INK, "lineWidth": 3, "radius": 16},
                "select": {"enabled": True, "lineColor": INK, "lineWidth": 4, "radius": 16},
            },
        },
        "allowPointSelect": True,
        "states": {"inactive": {"opacity": 0.3}},
    }
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "20px", "fontWeight": "normal", "color": INK_SOFT},
    "itemMarginBottom": 20,
    "symbolRadius": 10,
    "symbolHeight": 24,
    "symbolWidth": 24,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "borderRadius": 8,
}

# Tooltip
chart.options.tooltip = {
    "headerFormat": "<b>{series.name}</b><br>",
    "pointFormat": "X: {point.x:.1f}<br>Y: {point.y:.1f}",
    "style": {"fontSize": "18px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "borderWidth": 1,
}

# Credits
chart.options.credits = {"enabled": False}

# Add series for each cluster
for name, x, y, color in clusters:
    series = ScatterSeries()
    series.data = [[float(xi), float(yi)] for xi, yi in zip(x, y, strict=False)]
    series.name = name
    series.color = color
    series.marker = {"symbol": "circle", "fillColor": color, "lineWidth": 1, "lineColor": PAGE_BG}
    chart.add_series(series)

# Download Highcharts JS for inline embedding
# Try multiple CDN endpoints in case one is blocked
highcharts_urls = [
    "https://code.highcharts.com/highcharts.js",
    "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js",
]

highcharts_js = None
for url in highcharts_urls:
    try:
        request = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            highcharts_js = response.read().decode("utf-8")
            break
    except Exception:
        continue

if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS from any CDN")

# Generate JS literal for chart
html_str = chart.to_js_literal()

# Create HTML with inline Highcharts
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
<body style="background:{PAGE_BG};">
    <div id="container"></div>
    <script>
        {html_str}
    </script>
</body>
</html>"""

# Save interactive HTML version (theme-suffixed)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Generate PNG using Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
