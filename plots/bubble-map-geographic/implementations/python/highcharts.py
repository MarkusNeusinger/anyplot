""" pyplots.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
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


# Data - World city populations (realistic data)
np.random.seed(42)

# Major world cities with approximate populations (millions)
cities = [
    # Asia
    {"name": "Tokyo", "lat": 35.7, "lon": 139.7, "pop": 37.4, "continent": "Asia"},
    {"name": "Delhi", "lat": 28.6, "lon": 77.2, "pop": 32.9, "continent": "Asia"},
    {"name": "Shanghai", "lat": 31.2, "lon": 121.5, "pop": 29.2, "continent": "Asia"},
    {"name": "Beijing", "lat": 39.9, "lon": 116.4, "pop": 21.5, "continent": "Asia"},
    {"name": "Mumbai", "lat": 19.1, "lon": 72.9, "pop": 21.3, "continent": "Asia"},
    {"name": "Osaka", "lat": 34.7, "lon": 135.5, "pop": 19.0, "continent": "Asia"},
    {"name": "Dhaka", "lat": 23.8, "lon": 90.4, "pop": 23.2, "continent": "Asia"},
    {"name": "Karachi", "lat": 24.9, "lon": 67.1, "pop": 16.8, "continent": "Asia"},
    {"name": "Bangkok", "lat": 13.8, "lon": 100.5, "pop": 11.1, "continent": "Asia"},
    {"name": "Seoul", "lat": 37.6, "lon": 127.0, "pop": 9.9, "continent": "Asia"},
    {"name": "Jakarta", "lat": -6.2, "lon": 106.8, "pop": 11.2, "continent": "Asia"},
    {"name": "Manila", "lat": 14.6, "lon": 121.0, "pop": 14.4, "continent": "Asia"},
    {"name": "Singapore", "lat": 1.3, "lon": 103.8, "pop": 6.0, "continent": "Asia"},
    # Africa
    {"name": "Cairo", "lat": 30.0, "lon": 31.2, "pop": 21.8, "continent": "Africa"},
    {"name": "Lagos", "lat": 6.5, "lon": 3.4, "pop": 15.4, "continent": "Africa"},
    {"name": "Kinshasa", "lat": -4.3, "lon": 15.3, "pop": 17.0, "continent": "Africa"},
    {"name": "Johannesburg", "lat": -26.2, "lon": 28.0, "pop": 6.0, "continent": "Africa"},
    {"name": "Nairobi", "lat": -1.3, "lon": 36.8, "pop": 5.1, "continent": "Africa"},
    # Europe
    {"name": "London", "lat": 51.5, "lon": -0.1, "pop": 9.5, "continent": "Europe"},
    {"name": "Paris", "lat": 48.9, "lon": 2.3, "pop": 11.1, "continent": "Europe"},
    {"name": "Moscow", "lat": 55.8, "lon": 37.6, "pop": 12.6, "continent": "Europe"},
    {"name": "Istanbul", "lat": 41.0, "lon": 29.0, "pop": 15.6, "continent": "Europe"},
    {"name": "Madrid", "lat": 40.4, "lon": -3.7, "pop": 6.7, "continent": "Europe"},
    {"name": "Berlin", "lat": 52.5, "lon": 13.4, "pop": 3.6, "continent": "Europe"},
    # North America
    {"name": "New York", "lat": 40.7, "lon": -74.0, "pop": 18.9, "continent": "Americas"},
    {"name": "Mexico City", "lat": 19.4, "lon": -99.1, "pop": 21.8, "continent": "Americas"},
    {"name": "Los Angeles", "lat": 34.1, "lon": -118.2, "pop": 12.5, "continent": "Americas"},
    {"name": "Chicago", "lat": 41.9, "lon": -87.6, "pop": 8.9, "continent": "Americas"},
    {"name": "Toronto", "lat": 43.7, "lon": -79.4, "pop": 6.3, "continent": "Americas"},
    # South America
    {"name": "São Paulo", "lat": -23.5, "lon": -46.6, "pop": 22.4, "continent": "Americas"},
    {"name": "Buenos Aires", "lat": -34.6, "lon": -58.4, "pop": 15.4, "continent": "Americas"},
    {"name": "Rio de Janeiro", "lat": -22.9, "lon": -43.2, "pop": 13.6, "continent": "Americas"},
    {"name": "Bogotá", "lat": 4.6, "lon": -74.1, "pop": 11.3, "continent": "Americas"},
    {"name": "Lima", "lat": -12.0, "lon": -77.0, "pop": 11.0, "continent": "Americas"},
    # Oceania
    {"name": "Sydney", "lat": -33.9, "lon": 151.2, "pop": 5.4, "continent": "Oceania"},
    {"name": "Melbourne", "lat": -37.8, "lon": 145.0, "pop": 5.1, "continent": "Oceania"},
    {"name": "Auckland", "lat": -36.8, "lon": 174.8, "pop": 1.7, "continent": "Oceania"},
]

# Assign colorblind-safe colors by continent
continent_colors = {
    "Asia": "#306998",  # Python Blue
    "Africa": "#FFD43B",  # Python Yellow
    "Europe": "#9467BD",  # Purple
    "Americas": "#17BECF",  # Cyan
    "Oceania": "#8C564B",  # Brown
}

# Prepare data for mapbubble series - group by continent
continent_data = {}
for city in cities:
    continent = city["continent"]
    if continent not in continent_data:
        continent_data[continent] = []
    # z value is population - will be scaled by Highcharts
    continent_data[continent].append(
        {"name": city["name"], "lat": city["lat"], "lon": city["lon"], "z": city["pop"], "population": city["pop"]}
    )

# Build series list for Highcharts
series_list = []
for continent, data in continent_data.items():
    series_list.append(
        {
            "type": "mapbubble",
            "name": continent,
            "data": data,
            "color": continent_colors.get(continent, "#306998"),
            "marker": {"fillOpacity": 0.6, "lineWidth": 2, "lineColor": "#ffffff"},
            "minSize": 25,
            "maxSize": 120,
        }
    )

# Create JavaScript configuration for Highmaps with mapbubble
chart_config = {
    "chart": {
        "map": None,  # Will be set by topology
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "spacing": [120, 100, 80, 100],
    },
    "title": {
        "text": "World City Populations · bubble-map-geographic · highcharts · pyplots.ai",
        "style": {"fontSize": "56px", "fontWeight": "bold"},
        "y": 70,
    },
    "subtitle": {
        "text": "Bubble size proportional to metropolitan population (millions)",
        "style": {"fontSize": "40px", "color": "#666666"},
        "y": 120,
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
        "title": {"text": "Continent", "style": {"fontSize": "36px", "fontWeight": "bold"}},
        "symbolRadius": 10,
        "symbolHeight": 24,
        "symbolWidth": 24,
        "itemMarginBottom": 10,
    },
    "tooltip": {
        "useHTML": True,
        "headerFormat": '<span style="font-size: 32px; font-weight: bold;">{point.name}</span><br/>',
        "pointFormat": '<span style="font-size: 28px;">'
        "Continent: <b>{series.name}</b><br/>"
        "Population: <b>{point.population:.1f} million</b><br/>"
        "Location: ({point.lat:.1f}°, {point.lon:.1f}°)"
        "</span>",
    },
    "plotOptions": {
        "mapbubble": {
            "sizeBy": "area",  # Scale by area for accurate perception
            "zMin": 0,
            "zMax": 40,
            "dataLabels": {
                "enabled": False  # Keep clean, rely on tooltips
            },
        }
    },
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

# Generate HTML with inline scripts for headless rendering
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
