""" pyplots.ai
scatter-map-geographic: Scatter Map with Geographic Points
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Major earthquake epicenters (synthetic but realistic data)
np.random.seed(42)

# Generate earthquake data around tectonic plate boundaries
earthquakes = [
    # Pacific Ring of Fire - Japan
    {"lat": 38.3, "lon": 142.4, "mag": 9.1, "depth": 29, "region": "Japan"},
    {"lat": 36.1, "lon": 140.1, "mag": 7.3, "depth": 42, "region": "Japan"},
    {"lat": 40.8, "lon": 143.5, "mag": 6.8, "depth": 35, "region": "Japan"},
    # Pacific Ring of Fire - Chile/South America
    {"lat": -36.1, "lon": -72.9, "mag": 8.8, "depth": 35, "region": "South America"},
    {"lat": -33.2, "lon": -71.6, "mag": 7.8, "depth": 50, "region": "South America"},
    {"lat": -22.3, "lon": -68.9, "mag": 7.1, "depth": 112, "region": "South America"},
    {"lat": -15.5, "lon": -75.0, "mag": 8.0, "depth": 22, "region": "South America"},
    # Pacific Ring of Fire - Indonesia
    {"lat": 3.3, "lon": 95.8, "mag": 9.1, "depth": 30, "region": "Indonesia"},
    {"lat": -2.1, "lon": 99.6, "mag": 7.6, "depth": 25, "region": "Indonesia"},
    {"lat": -8.2, "lon": 115.5, "mag": 6.9, "depth": 18, "region": "Indonesia"},
    {"lat": -0.8, "lon": 131.1, "mag": 7.2, "depth": 15, "region": "Indonesia"},
    # Pacific Ring of Fire - Alaska/US West Coast
    {"lat": 61.0, "lon": -147.5, "mag": 9.2, "depth": 25, "region": "North America"},
    {"lat": 51.9, "lon": -176.1, "mag": 8.6, "depth": 33, "region": "North America"},
    {"lat": 35.8, "lon": -121.5, "mag": 6.9, "depth": 18, "region": "North America"},
    {"lat": 34.0, "lon": -118.2, "mag": 6.7, "depth": 12, "region": "North America"},
    # Mediterranean/Middle East
    {"lat": 38.5, "lon": 39.0, "mag": 7.8, "depth": 18, "region": "Mediterranean"},
    {"lat": 36.9, "lon": 27.5, "mag": 6.9, "depth": 21, "region": "Mediterranean"},
    {"lat": 37.0, "lon": 37.2, "mag": 7.5, "depth": 10, "region": "Mediterranean"},
    # Himalaya region
    {"lat": 28.2, "lon": 84.7, "mag": 7.8, "depth": 15, "region": "Asia"},
    {"lat": 26.9, "lon": 103.4, "mag": 6.9, "depth": 30, "region": "Asia"},
    {"lat": 30.0, "lon": 79.4, "mag": 7.0, "depth": 14, "region": "Asia"},
    # New Zealand/Pacific
    {"lat": -43.6, "lon": 172.5, "mag": 6.2, "depth": 5, "region": "Pacific"},
    {"lat": -37.5, "lon": 179.0, "mag": 7.1, "depth": 10, "region": "Pacific"},
    # Caribbean
    {"lat": 18.5, "lon": -72.5, "mag": 7.0, "depth": 13, "region": "Caribbean"},
    {"lat": 10.9, "lon": -85.9, "mag": 7.6, "depth": 20, "region": "Caribbean"},
    # Central Asia
    {"lat": 39.5, "lon": 76.9, "mag": 6.4, "depth": 22, "region": "Asia"},
    {"lat": 38.4, "lon": 73.1, "mag": 7.2, "depth": 33, "region": "Asia"},
    # Additional points for density
    {"lat": 45.5, "lon": 151.1, "mag": 6.6, "depth": 45, "region": "Japan"},
    {"lat": -5.8, "lon": 110.5, "mag": 6.3, "depth": 28, "region": "Indonesia"},
    {"lat": 52.5, "lon": -169.0, "mag": 7.4, "depth": 40, "region": "North America"},
]

# Assign colors by region for visual distinction
region_colors = {
    "Japan": "#DC2626",  # Red
    "South America": "#306998",  # Python Blue
    "Indonesia": "#F59E0B",  # Amber
    "North America": "#10B981",  # Emerald
    "Mediterranean": "#8B5CF6",  # Purple
    "Asia": "#FFD43B",  # Python Yellow
    "Pacific": "#06B6D4",  # Cyan
    "Caribbean": "#EC4899",  # Pink
}

# Prepare data for mapbubble series - group by region
regions_data = {}
for eq in earthquakes:
    region = eq["region"]
    if region not in regions_data:
        regions_data[region] = []
    # Calculate z (size) based on magnitude - exponential scale
    z_size = 10 ** (eq["mag"] - 5)  # Exponential scaling
    regions_data[region].append(
        {"lat": eq["lat"], "lon": eq["lon"], "z": z_size, "magnitude": eq["mag"], "depth": eq["depth"]}
    )

# Build series list for Highcharts
series_list = []
for region, data in regions_data.items():
    series_list.append(
        {
            "type": "mapbubble",
            "name": region,
            "data": data,
            "color": region_colors.get(region, "#306998"),
            "marker": {"fillOpacity": 0.7, "lineWidth": 2, "lineColor": "#ffffff"},
            "minSize": 20,
            "maxSize": 100,
        }
    )

# Create JavaScript configuration for Highmaps with mapbubble
chart_config = {
    "chart": {
        "map": None,  # Will be set by topology
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "spacing": [100, 100, 100, 100],
    },
    "title": {
        "text": "Global Earthquake Epicenters \u00b7 scatter-map-geographic \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "56px", "fontWeight": "bold"},
        "y": 60,
    },
    "subtitle": {
        "text": "Point size represents earthquake magnitude (exponential scale)",
        "style": {"fontSize": "40px", "color": "#666666"},
        "y": 110,
    },
    "mapNavigation": {"enabled": False},
    "legend": {
        "enabled": True,
        "layout": "vertical",
        "align": "right",
        "verticalAlign": "middle",
        "floating": True,
        "x": -50,
        "backgroundColor": "rgba(255, 255, 255, 0.95)",
        "borderColor": "#cccccc",
        "borderWidth": 2,
        "padding": 25,
        "itemStyle": {"fontSize": "32px"},
        "title": {"text": "Region", "style": {"fontSize": "36px", "fontWeight": "bold"}},
        "symbolRadius": 10,
        "symbolHeight": 24,
        "symbolWidth": 24,
        "itemMarginBottom": 10,
    },
    "tooltip": {
        "useHTML": True,
        "headerFormat": '<span style="font-size: 32px; font-weight: bold;">{series.name}</span><br/>',
        "pointFormat": '<span style="font-size: 28px;">'
        "Magnitude: <b>{point.magnitude}</b><br/>"
        "Depth: <b>{point.depth} km</b><br/>"
        "Location: ({point.lat:.1f}\u00b0, {point.lon:.1f}\u00b0)"
        "</span>",
    },
    "plotOptions": {"mapbubble": {"sizeBy": "area", "zMin": 1, "zMax": 10000}},
    "series": [
        {
            "type": "map",
            "name": "World",
            "showInLegend": False,
            "nullColor": "#e8e8e8",
            "borderColor": "#aaaaaa",
            "borderWidth": 1,
            "states": {"inactive": {"opacity": 1}},
        }
    ]
    + series_list,
}

# Convert to JSON for JavaScript
chart_json = json.dumps(chart_config)

# Download required JavaScript files
highmaps_url = "https://code.highcharts.com/maps/highmaps.js"
world_url = "https://code.highcharts.com/mapdata/custom/world.topo.json"

with urllib.request.urlopen(highmaps_url, timeout=60) as response:
    highmaps_js = response.read().decode("utf-8")

with urllib.request.urlopen(world_url, timeout=60) as response:
    world_topo = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        var topology = {world_topo};
        var chartConfig = {chart_json};
        chartConfig.chart.map = topology;
        Highcharts.mapChart('container', chartConfig);
    </script>
</body>
</html>"""

# Save HTML for interactive version
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/maps/highmaps.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        fetch('https://code.highcharts.com/mapdata/custom/world.topo.json')
            .then(response => response.json())
            .then(topology => {{
                var chartConfig = {chart_json};
                chartConfig.chart.map = topology;
                Highcharts.mapChart('container', chartConfig);
            }});
    </script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
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
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)  # Wait for chart to render (maps need more time)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
