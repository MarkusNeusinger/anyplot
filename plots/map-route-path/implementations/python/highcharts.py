""" pyplots.ai
map-route-path: Route Path Map
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2026-01-19
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Simulate a hiking trail GPS track through the Swiss Alps
np.random.seed(42)

# Generate a realistic hiking path through mountain terrain
# Start near Zermatt and traverse towards Mont Blanc region
n_points = 150

# Base path coordinates (starting near Zermatt, moving west)
base_lat = np.linspace(46.02, 45.92, n_points)
base_lon = np.linspace(7.75, 6.87, n_points)

# Add realistic GPS noise and terrain variation
lat_noise = np.cumsum(np.random.randn(n_points) * 0.002)
lon_noise = np.cumsum(np.random.randn(n_points) * 0.003)

# Create switchbacks (zigzag pattern for mountain climbing)
switchback = 0.01 * np.sin(np.linspace(0, 12 * np.pi, n_points))

lats = base_lat + lat_noise * 0.3 + switchback
lons = base_lon + lon_noise * 0.3

# Simulate elevation profile (climb then descend)
elevation = 1600 + 1200 * np.sin(np.linspace(0, np.pi, n_points)) + np.random.randn(n_points) * 50

# Create timestamps for the hike (6-hour hike)
start_time = 0  # hours
time_points = np.linspace(start_time, start_time + 6, n_points)

# Prepare waypoint data
waypoints = []
for i in range(n_points):
    waypoints.append(
        {
            "sequence": i + 1,
            "lat": float(lats[i]),
            "lon": float(lons[i]),
            "elevation": float(elevation[i]),
            "time_hrs": float(time_points[i]),
        }
    )

# Create path line data for mapline series
path_data = [[wp["lon"], wp["lat"]] for wp in waypoints]

# Calculate map bounds with padding for the route area
min_lat = min(lats)
max_lat = max(lats)
min_lon = min(lons)
max_lon = max(lons)

# Add small padding around the route (tighter bounds for better canvas utilization)
lat_padding = (max_lat - min_lat) * 0.15
lon_padding = (max_lon - min_lon) * 0.15
min_lat -= lat_padding
max_lat += lat_padding
min_lon -= lon_padding
max_lon += lon_padding

# Create color gradient segments for time progression
n_segments = 10
colors_gradient = [
    "#1a4f9c",  # Dark blue (start - 0 hrs)
    "#2166ac",
    "#4393c3",
    "#92c5de",
    "#d1e5f0",
    "#f7f7f7",
    "#fddbc7",
    "#f4a582",
    "#d6604d",
    "#b2182b",  # Red (end - 6 hrs)
]

# Build route segments data for gradient coloring
segment_size = n_points // n_segments
route_segments = []
for seg_idx in range(n_segments):
    start_idx = seg_idx * segment_size
    end_idx = min(start_idx + segment_size + 1, n_points)
    segment_coords = path_data[start_idx:end_idx]
    route_segments.append({"coordinates": segment_coords, "color": colors_gradient[seg_idx]})

# Create direction arrows at intervals along the path
arrow_indices = [30, 60, 90, 120]  # Indices where arrows appear
arrow_points = []
for idx in arrow_indices:
    if idx < n_points - 1:
        # Calculate direction angle from current point to next
        dx = lons[idx + 1] - lons[idx]
        dy = lats[idx + 1] - lats[idx]
        angle = np.degrees(np.arctan2(dy, dx))
        arrow_points.append({"lat": lats[idx], "lon": lons[idx], "angle": float(angle)})

# Waypoints for tooltip data (every 10th point)
waypoint_data = [
    {
        "lat": wp["lat"],
        "lon": wp["lon"],
        "sequence": wp["sequence"],
        "elevation": wp["elevation"],
        "time_hrs": wp["time_hrs"],
    }
    for wp in waypoints[::10]
]

# Start and end point data
start_point = waypoints[0]
end_point = waypoints[-1]

# Download required JavaScript files
highmaps_url = "https://code.highcharts.com/maps/highmaps.js"
switzerland_url = "https://code.highcharts.com/mapdata/countries/ch/ch-all.topo.json"

with urllib.request.urlopen(highmaps_url, timeout=60) as response:
    highmaps_js = response.read().decode("utf-8")

with urllib.request.urlopen(switzerland_url, timeout=60) as response:
    switzerland_topo = response.read().decode("utf-8")

# Convert data to JSON for embedding in HTML
route_segments_json = json.dumps(route_segments)
arrow_points_json = json.dumps(arrow_points)
waypoint_data_json = json.dumps(waypoint_data)
start_point_json = json.dumps(start_point)
end_point_json = json.dumps(end_point)

# Build the Highcharts configuration directly in JavaScript for full control
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
</head>
<body style="margin:0; background-color: #f0f4f8;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        var topology = {switzerland_topo};
        var routeSegments = {route_segments_json};
        var arrowPoints = {arrow_points_json};
        var waypointData = {waypoint_data_json};
        var startPoint = {start_point_json};
        var endPoint = {end_point_json};

        // Build series array
        var series = [];

        // 1. Base map (Switzerland)
        series.push({{
            type: 'map',
            name: 'Switzerland',
            mapData: topology,
            showInLegend: false,
            nullColor: '#e8e8e8',
            borderColor: '#aaaaaa',
            borderWidth: 1.5,
            states: {{ inactive: {{ opacity: 1 }} }}
        }});

        // 2. Route segments with color gradient
        routeSegments.forEach(function(seg, idx) {{
            series.push({{
                type: 'mapline',
                name: idx === 0 ? 'Route' : 'Route segment ' + idx,
                showInLegend: false,
                lineWidth: 18,
                color: seg.color,
                zIndex: 10 + idx,
                enableMouseTracking: false,
                data: [{{
                    geometry: {{
                        type: 'LineString',
                        coordinates: seg.coordinates
                    }}
                }}]
            }});
        }});

        // 3. Direction arrows along path
        var arrowData = arrowPoints.map(function(pt) {{
            return {{
                lat: pt.lat,
                lon: pt.lon,
                marker: {{
                    symbol: 'triangle',
                    radius: 16,
                    fillColor: '#306998',
                    lineWidth: 2,
                    lineColor: '#ffffff',
                    rotation: 90 - pt.angle
                }}
            }};
        }});
        series.push({{
            type: 'mappoint',
            name: 'Direction',
            showInLegend: false,
            color: '#306998',
            zIndex: 16,
            enableMouseTracking: false,
            data: arrowData
        }});

        // 4. Waypoints (small dots)
        series.push({{
            type: 'mappoint',
            name: 'Waypoints',
            showInLegend: false,
            color: '#FFD43B',
            zIndex: 15,
            marker: {{
                symbol: 'circle',
                radius: 12,
                fillColor: '#FFD43B',
                lineWidth: 2,
                lineColor: '#306998'
            }},
            data: waypointData
        }});

        // 5. Start marker
        series.push({{
            type: 'mappoint',
            name: 'Start (0 hrs)',
            showInLegend: true,
            color: '#10B981',
            zIndex: 20,
            marker: {{
                symbol: 'circle',
                radius: 28,
                fillColor: '#10B981',
                lineWidth: 4,
                lineColor: '#ffffff'
            }},
            dataLabels: {{
                enabled: true,
                format: 'START',
                style: {{ fontSize: '36px', fontWeight: 'bold', color: '#10B981', textOutline: '3px white' }},
                y: -50
            }},
            data: [{{ lat: startPoint.lat, lon: startPoint.lon }}]
        }});

        // 6. End marker
        series.push({{
            type: 'mappoint',
            name: 'End (6 hrs)',
            showInLegend: true,
            color: '#b2182b',
            zIndex: 20,
            marker: {{
                symbol: 'square',
                radius: 24,
                fillColor: '#b2182b',
                lineWidth: 4,
                lineColor: '#ffffff'
            }},
            dataLabels: {{
                enabled: true,
                format: 'END',
                style: {{ fontSize: '36px', fontWeight: 'bold', color: '#b2182b', textOutline: '3px white' }},
                y: -50
            }},
            data: [{{ lat: endPoint.lat, lon: endPoint.lon }}]
        }});

        // Create the map chart
        Highcharts.mapChart('container', {{
            chart: {{
                width: 4800,
                height: 2700,
                backgroundColor: '#f0f4f8',
                spacing: [100, 80, 80, 80]
            }},
            title: {{
                text: 'map-route-path · highcharts · pyplots.ai',
                style: {{ fontSize: '56px', fontWeight: 'bold' }},
                y: 60
            }},
            subtitle: {{
                text: 'Alpine Hiking Trail: GPS track from Zermatt region through the Swiss Alps (150 waypoints, 6-hour hike)<br>' +
                      '<span style="font-size: 28px; color: #666;">Route color: <span style="color: #1a4f9c;">■</span> Start (blue) → <span style="color: #b2182b;">■</span> End (red) = time progression</span>',
                useHTML: true,
                style: {{ fontSize: '36px', color: '#666666' }},
                y: 115
            }},
            mapNavigation: {{ enabled: false }},
            mapView: {{
                projection: {{ name: 'WebMercator' }},
                fitToGeometry: {{
                    type: 'Polygon',
                    coordinates: [[
                        [{min_lon}, {min_lat}],
                        [{max_lon}, {min_lat}],
                        [{max_lon}, {max_lat}],
                        [{min_lon}, {max_lat}],
                        [{min_lon}, {min_lat}]
                    ]]
                }},
                padding: [30, 30, 30, 30]
            }},
            legend: {{
                enabled: true,
                align: 'right',
                verticalAlign: 'top',
                layout: 'vertical',
                floating: true,
                x: -60,
                y: 180,
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: '#cccccc',
                borderWidth: 2,
                padding: 20,
                itemStyle: {{ fontSize: '28px' }},
                symbolWidth: 50,
                symbolHeight: 24,
                symbolRadius: 0,
                title: {{
                    text: 'Legend',
                    style: {{ fontSize: '32px', fontWeight: 'bold' }}
                }}
            }},
            colorAxis: {{
                min: 0,
                max: 6,
                stops: [
                    [0, '#1a4f9c'],
                    [0.2, '#4393c3'],
                    [0.4, '#92c5de'],
                    [0.5, '#f7f7f7'],
                    [0.6, '#fddbc7'],
                    [0.8, '#d6604d'],
                    [1, '#b2182b']
                ],
                labels: {{
                    format: '{{value}} hrs',
                    style: {{ fontSize: '28px' }}
                }},
                title: {{
                    text: 'Time (hours)',
                    style: {{ fontSize: '32px' }}
                }},
                layout: 'horizontal',
                floating: false,
                align: 'center',
                verticalAlign: 'bottom',
                y: -30,
                width: 900,
                height: 28
            }},
            tooltip: {{
                useHTML: true,
                headerFormat: '',
                pointFormat: '<span style="font-size: 24px;">' +
                    'Waypoint: <b>{{point.sequence}}</b><br/>' +
                    'Elevation: <b>{{point.elevation:.0f}}m</b><br/>' +
                    'Time: <b>{{point.time_hrs:.1f}} hrs</b>' +
                    '</span>'
            }},
            plotOptions: {{
                mappoint: {{ dataLabels: {{ enabled: false }} }},
                mapline: {{ lineWidth: 18, enableMouseTracking: false }}
            }},
            series: series
        }});
    </script>
</body>
</html>"""

# Save HTML for interactive version (standalone with CDN)
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/maps/highmaps.js"></script>
</head>
<body style="margin:0; background-color: #f0f4f8;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        var routeSegments = {route_segments_json};
        var arrowPoints = {arrow_points_json};
        var waypointData = {waypoint_data_json};
        var startPoint = {start_point_json};
        var endPoint = {end_point_json};

        fetch('https://code.highcharts.com/mapdata/countries/ch/ch-all.topo.json')
            .then(response => response.json())
            .then(function(topology) {{
                var series = [];

                series.push({{
                    type: 'map',
                    name: 'Switzerland',
                    mapData: topology,
                    showInLegend: false,
                    nullColor: '#e8e8e8',
                    borderColor: '#aaaaaa',
                    borderWidth: 1.5,
                    states: {{ inactive: {{ opacity: 1 }} }}
                }});

                routeSegments.forEach(function(seg, idx) {{
                    series.push({{
                        type: 'mapline',
                        name: idx === 0 ? 'Route' : 'Route segment ' + idx,
                        showInLegend: false,
                        lineWidth: 6,
                        color: seg.color,
                        zIndex: 10 + idx,
                        enableMouseTracking: false,
                        data: [{{ geometry: {{ type: 'LineString', coordinates: seg.coordinates }} }}]
                    }});
                }});

                var arrowData = arrowPoints.map(function(pt) {{
                    return {{
                        lat: pt.lat, lon: pt.lon,
                        marker: {{ symbol: 'triangle', radius: 8, fillColor: '#306998', lineWidth: 1, lineColor: '#ffffff', rotation: 90 - pt.angle }}
                    }};
                }});
                series.push({{ type: 'mappoint', name: 'Direction', showInLegend: false, color: '#306998', zIndex: 16, enableMouseTracking: false, data: arrowData }});

                series.push({{ type: 'mappoint', name: 'Waypoints', showInLegend: false, color: '#FFD43B', zIndex: 15, marker: {{ symbol: 'circle', radius: 5, fillColor: '#FFD43B', lineWidth: 1, lineColor: '#306998' }}, data: waypointData }});

                series.push({{ type: 'mappoint', name: 'Start (0 hrs)', showInLegend: true, color: '#10B981', zIndex: 20, marker: {{ symbol: 'circle', radius: 12, fillColor: '#10B981', lineWidth: 2, lineColor: '#ffffff' }}, dataLabels: {{ enabled: true, format: 'START', style: {{ fontSize: '14px', fontWeight: 'bold', color: '#10B981', textOutline: '2px white' }}, y: -20 }}, data: [{{ lat: startPoint.lat, lon: startPoint.lon }}] }});

                series.push({{ type: 'mappoint', name: 'End (6 hrs)', showInLegend: true, color: '#b2182b', zIndex: 20, marker: {{ symbol: 'square', radius: 10, fillColor: '#b2182b', lineWidth: 2, lineColor: '#ffffff' }}, dataLabels: {{ enabled: true, format: 'END', style: {{ fontSize: '14px', fontWeight: 'bold', color: '#b2182b', textOutline: '2px white' }}, y: -20 }}, data: [{{ lat: endPoint.lat, lon: endPoint.lon }}] }});

                Highcharts.mapChart('container', {{
                    chart: {{ backgroundColor: '#f0f4f8' }},
                    title: {{ text: 'map-route-path · highcharts · pyplots.ai' }},
                    subtitle: {{ text: 'Alpine Hiking Trail: GPS track from Zermatt region through the Swiss Alps (150 waypoints, 6-hour hike)<br><span style="font-size: 12px; color: #666;">Route color: blue (start) → red (end) = time progression</span>', useHTML: true }},
                    mapNavigation: {{ enabled: true }},
                    mapView: {{
                        projection: {{ name: 'WebMercator' }},
                        fitToGeometry: {{ type: 'Polygon', coordinates: [[[{min_lon}, {min_lat}], [{max_lon}, {min_lat}], [{max_lon}, {max_lat}], [{min_lon}, {max_lat}], [{min_lon}, {min_lat}]]] }},
                        padding: [20, 20, 20, 20]
                    }},
                    legend: {{ enabled: true, align: 'right', verticalAlign: 'top', layout: 'vertical', floating: true, title: {{ text: 'Legend' }} }},
                    colorAxis: {{ min: 0, max: 6, stops: [[0, '#1a4f9c'], [0.5, '#f7f7f7'], [1, '#b2182b']], labels: {{ format: '{{value}} hrs' }}, title: {{ text: 'Time (hours)' }} }},
                    tooltip: {{ useHTML: true, headerFormat: '', pointFormat: '<span>Waypoint: <b>{{point.sequence}}</b><br/>Elevation: <b>{{point.elevation:.0f}}m</b><br/>Time: <b>{{point.time_hrs:.1f}} hrs</b></span>' }},
                    series: series
                }});
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
time.sleep(6)  # Wait for map to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
