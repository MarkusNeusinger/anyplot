""" anyplot.ai
map-marker-clustered: Clustered Marker Map
Library: highcharts unknown | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-23
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
MAP_FILL = "#E8E4DB" if THEME == "light" else "#2A2A25"
MAP_BORDER = "#B0AC9F" if THEME == "light" else "#4A4A44"

# Imprint palette for the four store categories
CATEGORY_COLORS = {
    "Grocery": "#009E73",  # position 1 — brand green
    "Electronics": "#C475FD",  # position 2 — purple
    "Clothing": "#AE3030",  # position 3 — red
    "Home Goods": "#4467A3",  # position 4 — sky blue
}

# Data: retail stores clustered around 15 major US cities
np.random.seed(42)

cities = {
    "New York": (40.7128, -74.0060, 50),
    "Los Angeles": (34.0522, -118.2437, 45),
    "Chicago": (41.8781, -87.6298, 35),
    "Houston": (29.7604, -95.3698, 30),
    "Phoenix": (33.4484, -112.0740, 25),
    "Philadelphia": (39.9526, -75.1652, 20),
    "San Antonio": (29.4241, -98.4936, 18),
    "San Diego": (32.7157, -117.1611, 22),
    "Dallas": (32.7767, -96.7970, 28),
    "San Francisco": (37.7749, -122.4194, 25),
    "Seattle": (47.6062, -122.3321, 20),
    "Denver": (39.7392, -104.9903, 18),
    "Boston": (42.3601, -71.0589, 22),
    "Atlanta": (33.7490, -84.3880, 24),
    "Miami": (25.7617, -80.1918, 20),
}

categories = list(CATEGORY_COLORS.keys())
stores = []
for city_name, (lat, lon, count) in cities.items():
    for i in range(count):
        store_lat = lat + np.random.normal(0, 0.15)
        store_lon = lon + np.random.normal(0, 0.15)
        category = np.random.choice(categories)
        stores.append(
            {
                "lat": round(store_lat, 4),
                "lon": round(store_lon, 4),
                "name": f"{city_name} Store #{i + 1}",
                "category": category,
            }
        )

# Download required Highcharts modules (inline for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
maps_url = "https://code.highcharts.com/maps/modules/map.js"
marker_clusters_url = "https://code.highcharts.com/modules/marker-clusters.js"
us_map_url = "https://code.highcharts.com/mapdata/countries/us/us-all.topo.json"

_headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Referer": "https://www.highcharts.com/",
    "Accept": "*/*",
}

with urllib.request.urlopen(urllib.request.Request(highcharts_url, headers=_headers), timeout=30) as _r:
    highcharts_js = _r.read().decode("utf-8")

with urllib.request.urlopen(urllib.request.Request(maps_url, headers=_headers), timeout=30) as _r:
    maps_js = _r.read().decode("utf-8")

with urllib.request.urlopen(urllib.request.Request(marker_clusters_url, headers=_headers), timeout=30) as _r:
    marker_clusters_js = _r.read().decode("utf-8")

with urllib.request.urlopen(urllib.request.Request(us_map_url, headers=_headers), timeout=30) as _r:
    us_map_data = _r.read().decode("utf-8")

# Group stores by category for per-series clustering
series_by_category = {cat: [] for cat in categories}
for store in stores:
    series_by_category[store["category"]].append({"lat": store["lat"], "lon": store["lon"], "name": store["name"]})

# Build one mappoint series per category with clustering enabled
js_series_parts = []
for cat in categories:
    color = CATEGORY_COLORS[cat]
    data_json = json.dumps(series_by_category[cat])
    js_series_parts.append(f"""{{
            type: 'mappoint',
            name: '{cat}',
            color: '{color}',
            data: {data_json},
            dataLabels: {{
                enabled: true,
                allowOverlap: true,
                formatter: function() {{
                    if (this.point.isCluster) {{
                        return this.point.clusterPointsAmount;
                    }}
                    return '';
                }},
                style: {{
                    fontSize: '34px',
                    fontWeight: 'bold',
                    color: '#ffffff',
                    textOutline: '2px rgba(0,0,0,0.6)'
                }},
                y: 6
            }},
            cluster: {{
                enabled: true,
                allowOverlap: false,
                animation: {{ duration: 450 }},
                layoutAlgorithm: {{ type: 'grid', gridSize: 70 }},
                zones: [
                    {{ from: 1,  to: 4,   marker: {{ radius: 28 }} }},
                    {{ from: 5,  to: 9,   marker: {{ radius: 30 }} }},
                    {{ from: 10, to: 19,  marker: {{ radius: 38 }} }},
                    {{ from: 20, to: 49,  marker: {{ radius: 48 }} }},
                    {{ from: 50, to: 100, marker: {{ radius: 60 }} }}
                ]
            }},
            marker: {{ radius: 12, symbol: 'circle' }}
        }}""")

series_js = ",\n        ".join(js_series_parts)

store_count = len(stores)
subtitle_text = f"{store_count} store locations across 15 US cities \\u2014 zoom to expand clusters"

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{maps_js}</script>
    <script>{marker_clusters_js}</script>
</head>
<body style="margin:0; padding:0; background-color:{PAGE_BG};">
    <div id="container" style="width:3200px; height:1800px;"></div>
    <script>
        var mapData = {us_map_data};

        Highcharts.mapChart('container', {{
            chart: {{
                map: mapData,
                backgroundColor: '{PAGE_BG}',
                width: 3200,
                height: 1800,
                marginBottom: 60,
                style: {{ color: '{INK}' }}
            }},
            title: {{
                text: 'map-marker-clustered \\u00b7 python \\u00b7 highcharts \\u00b7 anyplot.ai',
                style: {{
                    fontSize: '66px',
                    fontWeight: 'bold',
                    color: '{INK}'
                }}
            }},
            subtitle: {{
                text: '{subtitle_text}',
                style: {{
                    fontSize: '36px',
                    color: '{INK_SOFT}'
                }}
            }},
            mapNavigation: {{
                enabled: true,
                buttonOptions: {{
                    verticalAlign: 'bottom',
                    style: {{
                        fontSize: '28px'
                    }}
                }}
            }},
            legend: {{
                enabled: true,
                align: 'right',
                verticalAlign: 'middle',
                layout: 'vertical',
                itemStyle: {{
                    fontSize: '40px',
                    color: '{INK_SOFT}'
                }},
                backgroundColor: '{ELEVATED_BG}',
                borderColor: '{INK_SOFT}',
                borderWidth: 1,
                padding: 24,
                symbolRadius: 50,
                symbolHeight: 36,
                symbolWidth: 36,
                itemMarginTop: 14,
                itemMarginBottom: 14
            }},
            tooltip: {{
                headerFormat: '',
                pointFormat: '<b>{{point.name}}</b><br>Category: {{series.name}}',
                clusterFormat: '<b>Cluster</b><br>Points: {{point.clusterPointsAmount}}',
                style: {{
                    fontSize: '32px'
                }}
            }},
            series: [{{
                name: 'US States',
                borderColor: '{MAP_BORDER}',
                nullColor: '{MAP_FILL}',
                showInLegend: false,
                enableMouseTracking: false
            }},
        {series_js}]
        }});
    </script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# PIL safety net: pin to exact 3200×1800 so the post-render gate is satisfied
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
