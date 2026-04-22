""" pyplots.ai
map-projections: World Map with Different Projections
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Create 4 different projection configurations to show comparison
# Highcharts supports: Miller, WebMercator, Orthographic, EqualEarth, and more
projections = [
    {
        "name": "Miller Cylindrical",
        "projection": {"name": "Miller"},
        "description": "Compromise between Mercator and equal-area",
    },
    {
        "name": "Equal Earth",
        "projection": {"name": "EqualEarth"},
        "description": "Equal-area projection, minimal distortion",
    },
    {
        "name": "Orthographic (Americas)",
        "projection": {"name": "Orthographic", "rotation": [90, 0]},
        "description": "Globe view centered on Americas",
    },
    {
        "name": "Orthographic (Africa/Europe)",
        "projection": {"name": "Orthographic", "rotation": [-20, -20]},
        "description": "Globe view centered on Africa/Europe",
    },
]

# Build the HTML with 4 charts in a 2x2 grid
chart_configs = []
for proj in projections:
    config = {
        "chart": {
            "map": None,  # Will be set by topology
            "backgroundColor": "#ffffff",
            "spacing": [20, 20, 20, 20],
        },
        "title": {"text": proj["name"], "style": {"fontSize": "48px", "fontWeight": "bold"}},
        "subtitle": {"text": proj["description"], "style": {"fontSize": "28px", "color": "#666666"}},
        "mapNavigation": {"enabled": False},
        "mapView": {"projection": proj["projection"]},
        "legend": {"enabled": False},
        "colorAxis": {"visible": False},
        "credits": {"enabled": False},
        "series": [
            {
                "type": "map",
                "name": "Countries",
                "showInLegend": False,
                "allAreas": True,
                "nullColor": "#306998",  # Python Blue for all land areas
                "borderColor": "#ffffff",
                "borderWidth": 2,
                "states": {
                    "hover": {"color": "#FFD43B"},  # Python Yellow on hover
                    "inactive": {"opacity": 1},
                },
            },
            {
                "type": "mapline",
                "name": "Graticule",
                "data": None,  # Will be generated
                "color": "#9467BD",  # Purple for contrast
                "lineWidth": 2,
                "dashStyle": "ShortDash",
                "enableMouseTracking": False,
                "showInLegend": False,
            },
        ],
    }
    chart_configs.append(config)

# Convert configs to JSON
configs_json = [json.dumps(config) for config in chart_configs]

# Download required JavaScript files
highmaps_url = "https://code.highcharts.com/maps/highmaps.js"
world_url = "https://code.highcharts.com/mapdata/custom/world.topo.json"
proj_url = "https://code.highcharts.com/maps/modules/proj4js.js"

with urllib.request.urlopen(highmaps_url, timeout=60) as response:
    highmaps_js = response.read().decode("utf-8")

with urllib.request.urlopen(world_url, timeout=60) as response:
    world_topo = response.read().decode("utf-8")

# Try to get proj4js for better projection support
try:
    with urllib.request.urlopen(proj_url, timeout=30) as response:
        proj4_js = response.read().decode("utf-8")
except Exception:
    proj4_js = ""  # Projection will use built-in support

# Generate graticule (lat/lon grid lines) as GeoJSON
graticule_features = []

# Longitude lines (meridians) every 30 degrees
for lon in range(-180, 181, 30):
    coords = [[lon, lat] for lat in range(-90, 91, 5)]
    graticule_features.append(
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {"name": f"{lon}°"},
        }
    )

# Latitude lines (parallels) every 30 degrees
for lat in range(-60, 61, 30):
    coords = [[lon, lat] for lon in range(-180, 181, 5)]
    graticule_features.append(
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {"name": f"{lat}°"},
        }
    )

graticule_geojson = {"type": "FeatureCollection", "features": graticule_features}
graticule_json = json.dumps(graticule_geojson)

# Generate HTML with 2x2 grid layout
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
    {f"<script>{proj4_js}</script>" if proj4_js else ""}
    <style>
        body {{
            margin: 0;
            padding: 60px;
            background: #ffffff;
            font-family: Arial, sans-serif;
        }}
        h1 {{
            text-align: center;
            font-size: 72px;
            margin-bottom: 20px;
            color: #333333;
        }}
        .subtitle {{
            text-align: center;
            font-size: 36px;
            color: #666666;
            margin-bottom: 60px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 40px;
            width: 4680px;
            height: 2300px;
        }}
        .chart-container {{
            background: #fafafa;
            border: 2px solid #dddddd;
            border-radius: 12px;
        }}
    </style>
</head>
<body>
    <h1>map-projections · highcharts · pyplots.ai</h1>
    <div class="subtitle">Comparing cartographic projections: how each transforms Earth's sphere to a flat map</div>
    <div class="grid">
        <div id="container0" class="chart-container"></div>
        <div id="container1" class="chart-container"></div>
        <div id="container2" class="chart-container"></div>
        <div id="container3" class="chart-container"></div>
    </div>
    <script>
        var topology = {world_topo};
        var graticule = {graticule_json};

        // Convert graticule to Highcharts format
        var graticuleData = Highcharts.geojson(graticule, 'mapline');

        var configs = [{configs_json[0]}, {configs_json[1]}, {configs_json[2]}, {configs_json[3]}];

        configs.forEach(function(config, i) {{
            config.chart.map = topology;
            config.chart.renderTo = 'container' + i;
            // Add graticule data to the mapline series
            config.series[1].data = graticuleData;
            Highcharts.mapChart(config);
        }});
    </script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/maps/highmaps.js"></script>
    <script src="https://code.highcharts.com/maps/modules/proj4js.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 40px;
            background: #ffffff;
            font-family: Arial, sans-serif;
        }}
        h1 {{
            text-align: center;
            font-size: 36px;
            margin-bottom: 10px;
            color: #333333;
        }}
        .subtitle {{
            text-align: center;
            font-size: 18px;
            color: #666666;
            margin-bottom: 30px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 20px;
            width: calc(100vw - 80px);
            height: calc(100vh - 200px);
        }}
        .chart-container {{
            background: #fafafa;
            border: 2px solid #dddddd;
            border-radius: 8px;
        }}
    </style>
</head>
<body>
    <h1>map-projections · highcharts · pyplots.ai</h1>
    <div class="subtitle">Comparing cartographic projections: how each transforms Earth's sphere to a flat map</div>
    <div class="grid">
        <div id="container0" class="chart-container"></div>
        <div id="container1" class="chart-container"></div>
        <div id="container2" class="chart-container"></div>
        <div id="container3" class="chart-container"></div>
    </div>
    <script>
        fetch('https://code.highcharts.com/mapdata/custom/world.topo.json')
            .then(response => response.json())
            .then(topology => {{
                var graticule = {graticule_json};
                var graticuleData = Highcharts.geojson(graticule, 'mapline');

                var configs = [{configs_json[0]}, {configs_json[1]}, {configs_json[2]}, {configs_json[3]}];

                configs.forEach(function(config, i) {{
                    config.chart.map = topology;
                    config.chart.renderTo = 'container' + i;
                    config.series[1].data = graticuleData;
                    Highcharts.mapChart(config);
                }});
            }});
    </script>
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
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(8)  # Wait for charts to render (multiple maps need more time)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
