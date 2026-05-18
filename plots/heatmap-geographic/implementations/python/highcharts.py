"""anyplot.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: highcharts | Python 3.13
Quality: 91/100 | Updated: 2026-05-18
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
LEGEND_BG = "rgba(255,253,246,0.95)" if THEME == "light" else "rgba(36,36,32,0.95)"

# Data - Activity density around San Francisco Bay Area
np.random.seed(42)

# Hotspot 1: Downtown SF
lat1 = np.random.normal(37.79, 0.02, 400)
lon1 = np.random.normal(-122.40, 0.02, 400)
val1 = np.random.uniform(0.6, 1.0, 400)

# Hotspot 2: Oakland
lat2 = np.random.normal(37.80, 0.025, 350)
lon2 = np.random.normal(-122.27, 0.025, 350)
val2 = np.random.uniform(0.5, 0.9, 350)

# Hotspot 3: Berkeley
lat3 = np.random.normal(37.87, 0.015, 250)
lon3 = np.random.normal(-122.26, 0.015, 250)
val3 = np.random.uniform(0.4, 0.8, 250)

# Hotspot 4: South SF / SFO corridor
lat4 = np.random.normal(37.65, 0.03, 300)
lon4 = np.random.normal(-122.40, 0.03, 300)
val4 = np.random.uniform(0.3, 0.7, 300)

# Scattered background points
lat_bg = np.random.uniform(37.5, 38.0, 200)
lon_bg = np.random.uniform(-122.6, -122.1, 200)
val_bg = np.random.uniform(0.1, 0.4, 200)

# Combine all data
latitudes = np.concatenate([lat1, lat2, lat3, lat4, lat_bg])
longitudes = np.concatenate([lon1, lon2, lon3, lon4, lon_bg])
values = np.concatenate([val1, val2, val3, val4, val_bg])

# Create gridded heatmap using binning and Gaussian smoothing
lat_min, lat_max = 37.45, 38.05
lon_min, lon_max = -122.65, -122.05
grid_size = 60

lat_bins = np.linspace(lat_min, lat_max, grid_size + 1)
lon_bins = np.linspace(lon_min, lon_max, grid_size + 1)
density_grid, _, _ = np.histogram2d(latitudes, longitudes, bins=[lat_bins, lon_bins], weights=values)

density_grid = gaussian_filter(density_grid, sigma=1.5)

density_max = density_grid.max()
if density_max > 0:
    density_grid = density_grid / density_max

# Build heatmap data points for Highcharts mappoint series
heatmap_data = []
lat_step = (lat_max - lat_min) / grid_size
lon_step = (lon_max - lon_min) / grid_size

for i in range(grid_size):
    for j in range(grid_size):
        intensity = density_grid[i, j]
        if intensity > 0.01:
            center_lat = lat_min + (i + 0.5) * lat_step
            center_lon = lon_min + (j + 0.5) * lon_step
            heatmap_data.append(
                {"lat": round(center_lat, 4), "lon": round(center_lon, 4), "z": round(float(intensity), 3)}
            )

# Chart configuration
chart_config = {
    "chart": {"map": None, "width": 4800, "height": 2700, "backgroundColor": PAGE_BG, "spacing": [100, 80, 60, 80]},
    "title": {
        "text": "Activity Density in SF Bay Area · heatmap-geographic · python · highcharts · anyplot.ai",
        "style": {"fontSize": "52px", "fontWeight": "bold", "color": INK},
        "y": 60,
    },
    "subtitle": {
        "text": "Spatial density visualization using kernel smoothing",
        "style": {"fontSize": "44px", "color": INK_SOFT},
        "y": 120,
    },
    "mapNavigation": {"enabled": False},
    "legend": {
        "enabled": True,
        "layout": "vertical",
        "align": "right",
        "verticalAlign": "middle",
        "floating": True,
        "x": -60,
        "backgroundColor": LEGEND_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 2,
        "padding": 30,
        "title": {"text": "Intensity", "style": {"fontSize": "42px", "fontWeight": "bold", "color": INK}},
        "symbolRadius": 0,
        "symbolHeight": 350,
        "symbolWidth": 40,
        "itemStyle": {"color": INK_SOFT, "fontSize": "32px"},
    },
    "colorAxis": {
        "min": 0,
        "max": 1,
        "stops": [
            [0, "rgba(255, 255, 178, 0.1)"],
            [0.2, "rgba(254, 204, 92, 0.5)"],
            [0.4, "rgba(253, 141, 60, 0.6)"],
            [0.6, "rgba(240, 59, 32, 0.7)"],
            [0.8, "rgba(189, 0, 38, 0.8)"],
            [1, "rgba(128, 0, 38, 0.9)"],
        ],
        "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}, "format": "{value:.1f}"},
    },
    "tooltip": {
        "useHTML": True,
        "headerFormat": "",
        "pointFormat": (
            '<span style="font-size: 28px;">'
            "Latitude: <b>{point.lat:.4f}°</b><br/>"
            "Longitude: <b>{point.lon:.4f}°</b><br/>"
            "Intensity: <b>{point.z:.2f}</b>"
            "</span>"
        ),
    },
    "mapView": {"projection": {"name": "WebMercator"}, "center": [-122.35, 37.75], "zoom": 9.5},
    "series": [
        {
            "type": "tiledwebmap",
            "name": "Basemap",
            "provider": {"type": "OpenStreetMap", "theme": "Standard"},
            "showInLegend": False,
        },
        {
            "type": "mappoint",
            "name": "Density",
            "data": heatmap_data,
            "colorKey": "z",
            "marker": {"symbol": "square", "radius": 24, "lineWidth": 0},
            "states": {"hover": {"brightness": 0.1}},
        },
    ],
}

chart_json = json.dumps(chart_config)

# Download required JavaScript files (jsdelivr — avoids CDN rate-limiting)
highmaps_url = "https://cdn.jsdelivr.net/npm/highcharts@12/highmaps.js"
tiledwebmap_url = "https://cdn.jsdelivr.net/npm/highcharts@12/modules/tiledwebmap.js"

with urllib.request.urlopen(highmaps_url, timeout=60) as response:
    highmaps_js = response.read().decode("utf-8")

with urllib.request.urlopen(tiledwebmap_url, timeout=60) as response:
    tiledwebmap_js = response.read().decode("utf-8")

# HTML with inline scripts for headless screenshot
inline_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
    <script>{tiledwebmap_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        var chartConfig = {chart_json};
        Highcharts.mapChart('container', chartConfig);
    </script>
</body>
</html>"""

# HTML with CDN links for interactive artifact
cdn_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/maps/highmaps.js"></script>
    <script src="https://code.highcharts.com/maps/modules/tiledwebmap.js"></script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        var chartConfig = {chart_json};
        Highcharts.mapChart('container', chartConfig);
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(cdn_html)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(inline_html)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(8)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
