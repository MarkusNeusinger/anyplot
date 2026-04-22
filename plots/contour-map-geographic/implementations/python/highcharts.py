""" pyplots.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-17
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Create elevation-like data over Western Europe
np.random.seed(42)

# Define geographic region (Western Europe - roughly Alps region)
lat_min, lat_max = 44.0, 50.0  # Latitude range (Switzerland/Alps area)
lon_min, lon_max = 5.0, 15.0  # Longitude range

# Create grid
grid_size = 50
lats = np.linspace(lat_min, lat_max, grid_size)
lons = np.linspace(lon_min, lon_max, grid_size)
LON, LAT = np.meshgrid(lons, lats)

# Simulate elevation data with mountain-like features
# Create peaks representing Alpine terrain
elevation = np.zeros_like(LON)

# Main Alpine ridge (roughly along lat 46-47)
alpine_ridge = 2500 * np.exp(-((LAT - 46.5) ** 2) / 0.8 - ((LON - 9.5) ** 2) / 4)

# Mont Blanc area peak (near Geneva)
mont_blanc = 3000 * np.exp(-((LAT - 45.8) ** 2) / 0.3 - ((LON - 6.9) ** 2) / 0.3)

# Matterhorn/Swiss Alps area
matterhorn = 2800 * np.exp(-((LAT - 46.0) ** 2) / 0.4 - ((LON - 7.7) ** 2) / 0.4)

# Austrian Alps
austrian_alps = 2200 * np.exp(-((LAT - 47.2) ** 2) / 0.6 - ((LON - 12.5) ** 2) / 1.5)

# Dolomites (Northern Italy)
dolomites = 2400 * np.exp(-((LAT - 46.4) ** 2) / 0.4 - ((LON - 11.8) ** 2) / 0.6)

# Combine all features with base terrain
elevation = alpine_ridge + mont_blanc + matterhorn + austrian_alps + dolomites
elevation += 200 + 100 * np.random.randn(*elevation.shape)  # Base + noise
elevation = np.clip(elevation, 0, 4000)  # Clip to realistic range


# Marching squares algorithm for contour extraction
def marching_squares_contour(Z, level, x_coords, y_coords):
    """Extract contour paths using marching squares with geographic coordinates."""
    rows, cols = Z.shape
    segments = []

    ms_table = {
        0: [],
        1: [[3, 2]],
        2: [[1, 2]],
        3: [[3, 1]],
        4: [[0, 1]],
        5: [[0, 3], [1, 2]],
        6: [[0, 2]],
        7: [[0, 3]],
        8: [[0, 3]],
        9: [[0, 2]],
        10: [[0, 1], [2, 3]],
        11: [[0, 1]],
        12: [[1, 3]],
        13: [[1, 2]],
        14: [[2, 3]],
        15: [],
    }

    for i in range(rows - 1):
        for j in range(cols - 1):
            tl = Z[i, j]
            tr = Z[i, j + 1]
            br = Z[i + 1, j + 1]
            bl = Z[i + 1, j]

            config = 0
            if tl >= level:
                config |= 8
            if tr >= level:
                config |= 4
            if br >= level:
                config |= 2
            if bl >= level:
                config |= 1

            edges = ms_table[config]
            if not edges:
                continue

            edge_points = {}

            # Top edge
            if tl != tr:
                t = (level - tl) / (tr - tl)
                if 0 <= t <= 1:
                    x_interp = x_coords[j] + t * (x_coords[j + 1] - x_coords[j])
                    edge_points[0] = (x_interp, y_coords[i])

            # Right edge
            if tr != br:
                t = (level - tr) / (br - tr)
                if 0 <= t <= 1:
                    y_interp = y_coords[i] + t * (y_coords[i + 1] - y_coords[i])
                    edge_points[1] = (x_coords[j + 1], y_interp)

            # Bottom edge
            if bl != br:
                t = (level - bl) / (br - bl)
                if 0 <= t <= 1:
                    x_interp = x_coords[j] + t * (x_coords[j + 1] - x_coords[j])
                    edge_points[2] = (x_interp, y_coords[i + 1])

            # Left edge
            if tl != bl:
                t = (level - tl) / (bl - tl)
                if 0 <= t <= 1:
                    y_interp = y_coords[i] + t * (y_coords[i + 1] - y_coords[i])
                    edge_points[3] = (x_coords[j], y_interp)

            for e1, e2 in edges:
                if e1 in edge_points and e2 in edge_points:
                    segments.append((edge_points[e1], edge_points[e2]))

    return segments


def connect_segments(segments):
    """Connect line segments into continuous paths."""
    if not segments:
        return []

    paths = []
    remaining = list(segments)

    while remaining:
        seg = remaining.pop(0)
        path = [seg[0], seg[1]]

        changed = True
        while changed:
            changed = False
            for i, seg in enumerate(remaining):
                if np.allclose(seg[0], path[-1], atol=0.001):
                    path.append(seg[1])
                    remaining.pop(i)
                    changed = True
                    break
                elif np.allclose(seg[1], path[-1], atol=0.001):
                    path.append(seg[0])
                    remaining.pop(i)
                    changed = True
                    break
                elif np.allclose(seg[1], path[0], atol=0.001):
                    path.insert(0, seg[0])
                    remaining.pop(i)
                    changed = True
                    break
                elif np.allclose(seg[0], path[0], atol=0.001):
                    path.insert(0, seg[1])
                    remaining.pop(i)
                    changed = True
                    break

        if len(path) >= 3:
            paths.append(path)

    return paths


# Extract contour lines at elevation intervals
contour_levels = [500, 1000, 1500, 2000, 2500, 3000]

# Colorblind-safe distinct colors for contour levels
level_colors = {
    500: "#2E7D32",  # Forest green for low
    1000: "#1565C0",  # Blue for mid-low
    1500: "#306998",  # Python blue for mid
    2000: "#7B1FA2",  # Purple for mid-high
    2500: "#C62828",  # Red-brown for high
    3000: "#FF6F00",  # Orange for peaks (high visibility)
}

# Collect all contour features for GeoJSON
all_features = []
label_data = []

for level in contour_levels:
    segments = marching_squares_contour(elevation, level, lons, lats)
    paths = connect_segments(segments)

    color = level_colors.get(level, "#306998")

    for path_idx, path in enumerate(paths):
        if len(path) < 3:
            continue

        # Subsample for performance
        step = max(1, len(path) // 80)
        subsampled = path[::step]
        if subsampled[-1] != path[-1]:
            subsampled.append(path[-1])

        # Format as [lon, lat] for GeoJSON
        coordinates = [[round(pt[0], 4), round(pt[1], 4)] for pt in subsampled]

        # Create GeoJSON feature
        feature = {
            "type": "Feature",
            "properties": {"level": level, "color": color, "name": f"{level}m"},
            "geometry": {"type": "LineString", "coordinates": coordinates},
        }
        all_features.append(feature)

        # Store label position for major contours
        if path_idx == 0 and level % 1000 == 0 and len(path) > 5:
            mid_pt = path[len(path) // 2]
            label_data.append({"lon": mid_pt[0], "lat": mid_pt[1], "level": level})

# Create GeoJSON FeatureCollection for contours
contours_geojson = {"type": "FeatureCollection", "features": all_features}

# Create contour series with individual styling
contour_series = []
legend_shown = set()

for feature in all_features:
    level = feature["properties"]["level"]
    color = feature["properties"]["color"]
    show_legend = level not in legend_shown
    if show_legend:
        legend_shown.add(level)

    contour_series.append(
        {
            "type": "mapline",
            "name": f"{level}m",
            "data": [{"geometry": feature["geometry"], "color": color}],
            "color": color,
            "nullColor": color,
            "lineWidth": 12 if level % 1000 == 0 else 6,
            "enableMouseTracking": True,
            "showInLegend": show_legend,
            "zIndex": 10 + (level // 500),  # Higher contours on top
            "states": {"inactive": {"opacity": 1}},
        }
    )

# Build Highmaps configuration
chart_config = {
    "chart": {
        "map": None,  # Will be set by topology
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#f0f8ff",
        "spacing": [100, 80, 100, 80],
    },
    "title": {
        "text": "Alpine Elevation Contours · contour-map-geographic · highcharts · pyplots.ai",
        "style": {"fontSize": "52px", "fontWeight": "bold"},
        "y": 60,
    },
    "subtitle": {
        "text": "Contour lines showing terrain elevation (meters) across the Alps region",
        "style": {"fontSize": "36px", "color": "#666666"},
        "y": 110,
    },
    "mapNavigation": {"enabled": False},
    "legend": {
        "enabled": True,
        "layout": "vertical",
        "align": "right",
        "verticalAlign": "middle",
        "floating": True,
        "x": -40,
        "backgroundColor": "rgba(255, 255, 255, 0.95)",
        "borderColor": "#cccccc",
        "borderWidth": 2,
        "padding": 20,
        "itemStyle": {"fontSize": "28px"},
        "title": {"text": "Elevation", "style": {"fontSize": "32px", "fontWeight": "bold"}},
        "symbolWidth": 40,
        "symbolHeight": 6,
        "itemMarginBottom": 8,
    },
    "tooltip": {
        "useHTML": True,
        "headerFormat": "",
        "pointFormat": '<span style="font-size: 28px;">Elevation: <b>{series.name}</b></span>',
    },
    "plotOptions": {"mapline": {"states": {"hover": {"lineWidth": 10, "color": "#FF6B6B"}}}},
    "series": [
        # Base map layer
        {
            "type": "map",
            "name": "Terrain",
            "showInLegend": False,
            "nullColor": "#d4e6c5",  # Land color (light green)
            "borderColor": "#888888",
            "borderWidth": 1,
            "states": {"inactive": {"opacity": 1}},
        }
    ]
    + contour_series,
}

chart_json = json.dumps(chart_config)

# Download required JavaScript files
highmaps_url = "https://code.highcharts.com/maps/highmaps.js"
europe_url = "https://code.highcharts.com/mapdata/custom/europe.topo.json"

with urllib.request.urlopen(highmaps_url, timeout=60) as response:
    highmaps_js = response.read().decode("utf-8")

with urllib.request.urlopen(europe_url, timeout=60) as response:
    europe_topo = response.read().decode("utf-8")

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
        var topology = {europe_topo};
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
        fetch('https://code.highcharts.com/mapdata/custom/europe.topo.json')
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
