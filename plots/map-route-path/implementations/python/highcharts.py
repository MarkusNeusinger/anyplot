""" anyplot.ai
map-route-path: Route Path Map
Library: highcharts unknown | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-21
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

# Map land/border colors (theme-adaptive warm neutrals)
MAP_LAND = "#E8E4DC" if THEME == "light" else "#2A2A25"
MAP_BORDER = "#B8B4A8" if THEME == "light" else "#4A4A42"
LEGEND_BG = "rgba(255,253,246,0.95)" if THEME == "light" else "rgba(36,36,32,0.95)"
LEGEND_BORDER = "#B8B4A8" if THEME == "light" else "#4A4A42"

# Data — Swiss Alps hiking trail from Zermatt region
np.random.seed(42)
n_points = 150

# Base path: Zermatt area moving westward
base_lat = np.linspace(46.02, 45.92, n_points)
base_lon = np.linspace(7.75, 6.87, n_points)

# Realistic GPS noise and switchbacks (mountain terrain)
lat_noise = np.cumsum(np.random.randn(n_points) * 0.002)
lon_noise = np.cumsum(np.random.randn(n_points) * 0.003)
switchback = 0.01 * np.sin(np.linspace(0, 12 * np.pi, n_points))

lats = base_lat + lat_noise * 0.3 + switchback
lons = base_lon + lon_noise * 0.3

# Elevation profile (climb then descend, realistic Alpine values)
elevation = 1600 + 1200 * np.sin(np.linspace(0, np.pi, n_points)) + np.random.randn(n_points) * 50

# 6-hour hike timestamps
time_points = np.linspace(0, 6, n_points)

# Build waypoint records
waypoints = [
    {
        "sequence": i + 1,
        "lat": float(lats[i]),
        "lon": float(lons[i]),
        "elevation": float(elevation[i]),
        "time_hrs": float(time_points[i]),
    }
    for i in range(n_points)
]

# Path coordinates for mapline series [lon, lat]
path_data = [[wp["lon"], wp["lat"]] for wp in waypoints]

# Map bounding box — asymmetric: extend north into Switzerland to fill the 16:9 canvas
_lat_range = max(lats) - min(lats)
_lon_range = max(lons) - min(lons)
min_lat = min(lats) - _lat_range * 0.1
max_lat = max(lats) + _lat_range * 3.0
min_lon = min(lons) - _lon_range * 0.7
max_lon = max(lons) + _lon_range * 0.7

# Route segments colored by time (viridis — perceptually uniform sequential)
n_segments = 10
gradient_colors = [
    "#440154",
    "#482878",
    "#3e4989",
    "#31688e",
    "#26828e",
    "#1f9e89",
    "#35b779",
    "#6ece58",
    "#b5de2b",
    "#fde725",
]
segment_size = n_points // n_segments
route_segments = []
for seg_idx in range(n_segments):
    s = seg_idx * segment_size
    e = min(s + segment_size + 1, n_points)
    route_segments.append({"coordinates": path_data[s:e], "color": gradient_colors[seg_idx]})

# Direction arrows at four waypoints along the trail
arrow_indices = [30, 60, 90, 120]
arrow_points = []
for idx in arrow_indices:
    if idx < n_points - 1:
        dx = lons[idx + 1] - lons[idx]
        dy = lats[idx + 1] - lats[idx]
        angle = float(np.degrees(np.arctan2(dy, dx)))
        arrow_points.append({"lat": float(lats[idx]), "lon": float(lons[idx]), "angle": angle})

# Tooltip waypoints (every 10th point)
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

start_point = waypoints[0]
end_point = waypoints[-1]

# Download Highmaps JS and Switzerland topology
# (raw JS is necessary for Highmaps geographic features not available in highcharts_core)
# jsdelivr used for highmaps.js — highcharts CDN blocks non-browser user-agents
_ua = {"User-Agent": "Mozilla/5.0"}

_req = urllib.request.Request("https://cdn.jsdelivr.net/npm/highcharts@10.3.3/highmaps.js", headers=_ua)
with urllib.request.urlopen(_req, timeout=60) as _resp:
    highmaps_js = _resp.read().decode("utf-8")

_req = urllib.request.Request("https://code.highcharts.com/mapdata/countries/ch/ch-all.topo.json", headers=_ua)
with urllib.request.urlopen(_req, timeout=60) as _resp:
    switzerland_topo = _resp.read().decode("utf-8")

# Serialize data for JS embedding
route_segments_json = json.dumps(route_segments)
arrow_points_json = json.dumps(arrow_points)
waypoint_data_json = json.dumps(waypoint_data)
start_point_json = json.dumps(start_point)
end_point_json = json.dumps(end_point)

# Inline HTML for Selenium screenshot (canvas exactly 3200×1800)
html_inline = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:3200px; height:1800px;"></div>
    <script>
        var topology = {switzerland_topo};
        var routeSegments = {route_segments_json};
        var arrowPoints = {arrow_points_json};
        var waypointData = {waypoint_data_json};
        var startPoint = {start_point_json};
        var endPoint = {end_point_json};

        var series = [];

        // 1. Switzerland basemap
        series.push({{
            type: 'map',
            name: 'Switzerland',
            mapData: topology,
            showInLegend: false,
            nullColor: '{MAP_LAND}',
            borderColor: '{MAP_BORDER}',
            borderWidth: 1.5,
            states: {{ inactive: {{ opacity: 1 }} }}
        }});

        // 2. Route segments — viridis gradient encodes time elapsed
        routeSegments.forEach(function(seg, idx) {{
            series.push({{
                type: 'mapline',
                name: idx === 0 ? 'Route (0 h)' : (idx === routeSegments.length - 1 ? 'Route (6 h)' : 'Route ' + (idx + 1)),
                showInLegend: (idx === 0 || idx === routeSegments.length - 1),
                lineWidth: 16,
                color: seg.color,
                zIndex: 10 + idx,
                enableMouseTracking: false,
                data: [{{
                    geometry: {{ type: 'LineString', coordinates: seg.coordinates }}
                }}]
            }});
        }});

        // 3. Direction arrows (Okabe-Ito blue)
        var arrowData = arrowPoints.map(function(pt) {{
            return {{
                lat: pt.lat, lon: pt.lon,
                marker: {{
                    symbol: 'triangle',
                    radius: 14,
                    fillColor: '#0072B2',
                    lineWidth: 2,
                    lineColor: '{PAGE_BG}',
                    rotation: 90 - pt.angle
                }}
            }};
        }});
        series.push({{
            type: 'mappoint',
            name: 'Direction',
            showInLegend: false,
            zIndex: 16,
            enableMouseTracking: false,
            data: arrowData
        }});

        // 4. Waypoint dots (Okabe-Ito orange)
        series.push({{
            type: 'mappoint',
            name: 'Waypoints',
            showInLegend: false,
            zIndex: 15,
            marker: {{
                symbol: 'circle',
                radius: 8,
                fillColor: '#E69F00',
                lineWidth: 2,
                lineColor: '{PAGE_BG}'
            }},
            data: waypointData
        }});

        // 5. Start marker — Okabe-Ito green circle
        series.push({{
            type: 'mappoint',
            name: 'Start (0 hrs)',
            showInLegend: true,
            color: '#009E73',
            zIndex: 20,
            marker: {{
                symbol: 'circle',
                radius: 22,
                fillColor: '#009E73',
                lineWidth: 4,
                lineColor: '{PAGE_BG}'
            }},
            dataLabels: {{
                enabled: true,
                format: 'START',
                style: {{
                    fontSize: '38px',
                    fontWeight: 'bold',
                    color: '#009E73',
                    textOutline: '3px {PAGE_BG}'
                }},
                y: -50
            }},
            data: [{{ lat: startPoint.lat, lon: startPoint.lon }}]
        }});

        // 6. End marker — Okabe-Ito vermillion square
        series.push({{
            type: 'mappoint',
            name: 'End (6 hrs)',
            showInLegend: true,
            color: '#D55E00',
            zIndex: 20,
            marker: {{
                symbol: 'square',
                radius: 18,
                fillColor: '#D55E00',
                lineWidth: 4,
                lineColor: '{PAGE_BG}'
            }},
            dataLabels: {{
                enabled: true,
                format: 'END',
                style: {{
                    fontSize: '38px',
                    fontWeight: 'bold',
                    color: '#D55E00',
                    textOutline: '3px {PAGE_BG}'
                }},
                y: -50
            }},
            data: [{{ lat: endPoint.lat, lon: endPoint.lon }}]
        }});

        Highcharts.mapChart('container', {{
            chart: {{
                width: 3200,
                height: 1800,
                backgroundColor: '{PAGE_BG}',
                spacingTop: 80,
                spacingBottom: 40,
                spacingLeft: 60,
                spacingRight: 60,
                marginBottom: 60
            }},
            title: {{
                text: 'map-route-path · python · highcharts · anyplot.ai',
                style: {{ fontSize: '66px', fontWeight: 'bold', color: '{INK}' }},
                y: 50
            }},
            subtitle: {{
                text: 'Alpine Hiking Trail · Swiss Alps, Zermatt region · 150 GPS waypoints over 6 hours · route color = time elapsed',
                style: {{ fontSize: '38px', color: '{INK_SOFT}' }},
                y: 130
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
                padding: [20, 20, 20, 20]
            }},
            legend: {{
                enabled: true,
                align: 'right',
                verticalAlign: 'top',
                layout: 'vertical',
                floating: true,
                x: -50,
                y: 200,
                backgroundColor: '{LEGEND_BG}',
                borderColor: '{LEGEND_BORDER}',
                borderWidth: 1,
                padding: 24,
                itemStyle: {{
                    fontSize: '40px',
                    color: '{INK_SOFT}',
                    fontWeight: 'normal'
                }},
                symbolWidth: 44,
                symbolHeight: 22,
                title: {{
                    text: 'Markers',
                    style: {{ fontSize: '40px', fontWeight: 'bold', color: '{INK}' }}
                }}
            }},
            colorAxis: {{ enabled: false }},
            tooltip: {{
                useHTML: true,
                headerFormat: '',
                pointFormat: '<span style="font-size:28px;">' +
                    'Waypoint: <b>{{point.sequence}}</b><br/>' +
                    'Elevation: <b>{{point.elevation:.0f}} m</b><br/>' +
                    'Time: <b>{{point.time_hrs:.1f}} hrs</b>' +
                    '</span>'
            }},
            plotOptions: {{
                mappoint: {{ dataLabels: {{ enabled: false }} }},
                mapline: {{ enableMouseTracking: false }}
            }},
            series: series
        }});
    </script>
</body>
</html>"""

# Interactive HTML artifact — CDN version for the website
html_cdn = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@10.3.3/highmaps.js"></script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:100%; height:100vh;"></div>
    <script>
        var routeSegments = {route_segments_json};
        var arrowPoints = {arrow_points_json};
        var waypointData = {waypoint_data_json};
        var startPoint = {start_point_json};
        var endPoint = {end_point_json};

        fetch('https://code.highcharts.com/mapdata/countries/ch/ch-all.topo.json')
            .then(r => r.json())
            .then(function(topology) {{
                var series = [];
                series.push({{
                    type: 'map', name: 'Switzerland', mapData: topology,
                    showInLegend: false, nullColor: '{MAP_LAND}',
                    borderColor: '{MAP_BORDER}', borderWidth: 1,
                    states: {{ inactive: {{ opacity: 1 }} }}
                }});
                routeSegments.forEach(function(seg, idx) {{
                    series.push({{
                        type: 'mapline', name: idx === 0 ? 'Route' : 'Route ' + (idx + 1),
                        showInLegend: false, lineWidth: 5, color: seg.color,
                        zIndex: 10 + idx, enableMouseTracking: false,
                        data: [{{ geometry: {{ type: 'LineString', coordinates: seg.coordinates }} }}]
                    }});
                }});
                var arrowData = arrowPoints.map(function(pt) {{
                    return {{
                        lat: pt.lat, lon: pt.lon,
                        marker: {{ symbol: 'triangle', radius: 7, fillColor: '#0072B2',
                                   lineWidth: 1, lineColor: '#fff', rotation: 90 - pt.angle }}
                    }};
                }});
                series.push({{ type: 'mappoint', name: 'Direction', showInLegend: false,
                               zIndex: 16, enableMouseTracking: false, data: arrowData }});
                series.push({{ type: 'mappoint', name: 'Waypoints', showInLegend: false,
                               zIndex: 15, marker: {{ symbol: 'circle', radius: 4,
                               fillColor: '#E69F00', lineWidth: 1, lineColor: '#fff' }},
                               data: waypointData }});
                series.push({{
                    type: 'mappoint', name: 'Start (0 hrs)', showInLegend: true,
                    color: '#009E73', zIndex: 20,
                    marker: {{ symbol: 'circle', radius: 11, fillColor: '#009E73',
                               lineWidth: 2, lineColor: '#fff' }},
                    dataLabels: {{ enabled: true, format: 'START',
                                   style: {{ fontSize: '13px', fontWeight: 'bold',
                                             color: '#009E73', textOutline: '2px #fff' }}, y: -22 }},
                    data: [{{ lat: startPoint.lat, lon: startPoint.lon }}]
                }});
                series.push({{
                    type: 'mappoint', name: 'End (6 hrs)', showInLegend: true,
                    color: '#D55E00', zIndex: 20,
                    marker: {{ symbol: 'square', radius: 9, fillColor: '#D55E00',
                               lineWidth: 2, lineColor: '#fff' }},
                    dataLabels: {{ enabled: true, format: 'END',
                                   style: {{ fontSize: '13px', fontWeight: 'bold',
                                             color: '#D55E00', textOutline: '2px #fff' }}, y: -22 }},
                    data: [{{ lat: endPoint.lat, lon: endPoint.lon }}]
                }});
                Highcharts.mapChart('container', {{
                    chart: {{ backgroundColor: '{PAGE_BG}' }},
                    title: {{ text: 'map-route-path · python · highcharts · anyplot.ai',
                              style: {{ color: '{INK}' }} }},
                    subtitle: {{ text: 'Alpine Hiking Trail · Swiss Alps · 6-hour GPS track · color = time elapsed',
                                 style: {{ color: '{INK_SOFT}' }} }},
                    mapNavigation: {{ enabled: true }},
                    mapView: {{
                        projection: {{ name: 'WebMercator' }},
                        fitToGeometry: {{ type: 'Polygon', coordinates: [[[{min_lon}, {min_lat}],
                            [{max_lon}, {min_lat}], [{max_lon}, {max_lat}],
                            [{min_lon}, {max_lat}], [{min_lon}, {min_lat}]]] }},
                        padding: [20, 20, 20, 20]
                    }},
                    legend: {{ enabled: true, align: 'right', verticalAlign: 'top',
                               layout: 'vertical', floating: true }},
                    colorAxis: {{ enabled: false }},
                    tooltip: {{ useHTML: true, headerFormat: '',
                                pointFormat: '<span>Waypoint: <b>{{point.sequence}}</b><br/>' +
                                'Elevation: <b>{{point.elevation:.0f}} m</b><br/>' +
                                'Time: <b>{{point.time_hrs:.1f}} hrs</b></span>' }},
                    series: series
                }});
            }});
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_cdn)

# Screenshot via headless Chrome (exact 3200×1800 viewport via CDP override)
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_inline)
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

# Belt-and-braces: pin to exact 3200×1800 (CDP rounding can drift ±2 px)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
