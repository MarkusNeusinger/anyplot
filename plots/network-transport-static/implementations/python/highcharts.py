""" pyplots.ai
network-transport-static: Static Transport Network Diagram
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2026-01-10
"""

import json
import math
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Regional Rail Network (normalized coordinates 0-100)
stations = [
    {"id": "central", "label": "Central Station", "x": 50, "y": 50},
    {"id": "north", "label": "North Terminal", "x": 50, "y": 15},
    {"id": "south", "label": "South Harbor", "x": 50, "y": 85},
    {"id": "east", "label": "East Junction", "x": 80, "y": 50},
    {"id": "west", "label": "West Plaza", "x": 20, "y": 50},
    {"id": "ne", "label": "Northeast Park", "x": 70, "y": 22},
    {"id": "nw", "label": "Northwest Mall", "x": 30, "y": 22},
    {"id": "se", "label": "Southeast Tech", "x": 70, "y": 78},
    {"id": "sw", "label": "Southwest Arena", "x": 30, "y": 78},
    {"id": "airport", "label": "Airport", "x": 92, "y": 30},
    {"id": "university", "label": "University", "x": 12, "y": 74},
    {"id": "industrial", "label": "Industrial Zone", "x": 88, "y": 67},
]

routes = [
    {
        "source_id": "central",
        "target_id": "north",
        "route_id": "RE 1",
        "departure_time": "06:00",
        "arrival_time": "06:25",
    },
    {
        "source_id": "north",
        "target_id": "central",
        "route_id": "RE 1",
        "departure_time": "06:30",
        "arrival_time": "06:55",
    },
    {
        "source_id": "central",
        "target_id": "south",
        "route_id": "RE 2",
        "departure_time": "07:00",
        "arrival_time": "07:30",
    },
    {
        "source_id": "south",
        "target_id": "central",
        "route_id": "RE 2",
        "departure_time": "07:45",
        "arrival_time": "08:15",
    },
    {
        "source_id": "central",
        "target_id": "east",
        "route_id": "EX 10",
        "departure_time": "06:15",
        "arrival_time": "06:35",
    },
    {
        "source_id": "east",
        "target_id": "central",
        "route_id": "EX 10",
        "departure_time": "07:00",
        "arrival_time": "07:20",
    },
    {
        "source_id": "central",
        "target_id": "west",
        "route_id": "RE 3",
        "departure_time": "06:30",
        "arrival_time": "06:55",
    },
    {
        "source_id": "west",
        "target_id": "central",
        "route_id": "RE 3",
        "departure_time": "07:10",
        "arrival_time": "07:35",
    },
    {"source_id": "north", "target_id": "ne", "route_id": "LC 5", "departure_time": "08:00", "arrival_time": "08:20"},
    {
        "source_id": "ne",
        "target_id": "airport",
        "route_id": "EX 15",
        "departure_time": "08:30",
        "arrival_time": "08:50",
    },
    {
        "source_id": "airport",
        "target_id": "east",
        "route_id": "EX 15",
        "departure_time": "09:00",
        "arrival_time": "09:25",
    },
    {"source_id": "north", "target_id": "nw", "route_id": "LC 4", "departure_time": "07:45", "arrival_time": "08:05"},
    {"source_id": "nw", "target_id": "west", "route_id": "LC 4", "departure_time": "08:15", "arrival_time": "08:40"},
    {"source_id": "south", "target_id": "se", "route_id": "LC 6", "departure_time": "09:00", "arrival_time": "09:20"},
    {
        "source_id": "se",
        "target_id": "industrial",
        "route_id": "LC 6",
        "departure_time": "09:30",
        "arrival_time": "09:55",
    },
    {"source_id": "south", "target_id": "sw", "route_id": "LC 7", "departure_time": "08:30", "arrival_time": "08:55"},
    {
        "source_id": "sw",
        "target_id": "university",
        "route_id": "LC 7",
        "departure_time": "09:05",
        "arrival_time": "09:35",
    },
    {
        "source_id": "east",
        "target_id": "industrial",
        "route_id": "RE 8",
        "departure_time": "10:00",
        "arrival_time": "10:20",
    },
    {
        "source_id": "west",
        "target_id": "university",
        "route_id": "RE 9",
        "departure_time": "10:30",
        "arrival_time": "10:55",
    },
]

# Build station lookup
station_lookup = {s["id"]: s for s in stations}

# Route type colors
route_colors = {
    "EX": "#306998",  # Express - Python Blue
    "RE": "#FFD43B",  # Regional - Python Yellow
    "LC": "#9467BD",  # Local - Purple
}


# Build series data for routes
route_series_list = []
route_pair_offset = {}

for route in routes:
    source = station_lookup[route["source_id"]]
    target = station_lookup[route["target_id"]]

    pair = tuple(sorted([route["source_id"], route["target_id"]]))
    if pair not in route_pair_offset:
        route_pair_offset[pair] = 0

    offset_amount = route_pair_offset[pair] * 1.5
    route_pair_offset[pair] += 1

    dx = target["x"] - source["x"]
    dy = target["y"] - source["y"]
    length = (dx**2 + dy**2) ** 0.5
    if length > 0:
        perp_x = -dy / length * offset_amount
        perp_y = dx / length * offset_amount
    else:
        perp_x, perp_y = 0, 0

    sx = source["x"] + perp_x
    sy = source["y"] + perp_y
    tx = target["x"] + perp_x
    ty = target["y"] + perp_y

    route_prefix = route["route_id"].split()[0]
    color = route_colors.get(route_prefix, "#17BECF")
    label_text = f"{route['route_id']} | {route['departure_time']} → {route['arrival_time']}"

    route_series_list.append(
        {
            "type": "line",
            "name": label_text,
            "data": [[sx, sy], [tx, ty]],
            "color": color,
            "lineWidth": 5,
            "marker": {"enabled": False},
            "enableMouseTracking": True,
            "showInLegend": False,
            "zIndex": 1,
        }
    )

# Build station series
station_data = []
for station in stations:
    station_data.append({"x": station["x"], "y": station["y"], "name": station["label"]})

station_series = {
    "type": "scatter",
    "name": "Stations",
    "data": station_data,
    "marker": {"radius": 22, "symbol": "circle", "fillColor": "#ffffff", "lineWidth": 5, "lineColor": "#306998"},
    "dataLabels": {
        "enabled": True,
        "format": "{point.name}",
        "style": {"fontSize": "24px", "fontWeight": "bold", "textOutline": "3px white"},
        "y": -40,
    },
    "zIndex": 10,
    "showInLegend": False,
}

# Build annotations for route labels
annotations_list = []
route_pair_offset = {}

for route in routes:
    source = station_lookup[route["source_id"]]
    target = station_lookup[route["target_id"]]

    pair = tuple(sorted([route["source_id"], route["target_id"]]))
    if pair not in route_pair_offset:
        route_pair_offset[pair] = 0

    offset_amount = route_pair_offset[pair] * 1.5
    route_pair_offset[pair] += 1

    dx = target["x"] - source["x"]
    dy = target["y"] - source["y"]
    length = (dx**2 + dy**2) ** 0.5
    if length > 0:
        perp_x = -dy / length * offset_amount
        perp_y = dx / length * offset_amount
    else:
        perp_x, perp_y = 0, 0

    sx = source["x"] + perp_x
    sy = source["y"] + perp_y
    tx = target["x"] + perp_x
    ty = target["y"] + perp_y

    mid_x = (sx + tx) / 2
    mid_y = (sy + ty) / 2

    route_prefix = route["route_id"].split()[0]
    color = route_colors.get(route_prefix, "#17BECF")
    text_color = "#ffffff" if color != "#FFD43B" else "#000000"
    label_text = f"{route['route_id']} | {route['departure_time']} \u2192 {route['arrival_time']}"

    annotations_list.append(
        {
            "labels": [
                {
                    "point": {"x": mid_x, "y": mid_y, "xAxis": 0, "yAxis": 0},
                    "text": label_text,
                    "backgroundColor": color,
                    "borderColor": color,
                    "style": {"color": text_color, "fontSize": "16px", "fontWeight": "bold"},
                    "padding": 5,
                    "borderRadius": 4,
                }
            ],
            "draggable": "",
        }
    )

    # Arrow at 75% - use HTML triangle symbols for reliable rendering
    arrow_x = sx + (tx - sx) * 0.75
    arrow_y = sy + (ty - sy) * 0.75
    angle = math.degrees(math.atan2(ty - sy, tx - sx))

    if -45 <= angle < 45:
        arrow_html = "\u25b6"  # Right-pointing triangle
    elif 45 <= angle < 135:
        arrow_html = "\u25bc"  # Down-pointing triangle
    elif -135 <= angle < -45:
        arrow_html = "\u25b2"  # Up-pointing triangle
    else:
        arrow_html = "\u25c0"  # Left-pointing triangle

    annotations_list.append(
        {
            "labels": [
                {
                    "point": {"x": arrow_x, "y": arrow_y, "xAxis": 0, "yAxis": 0},
                    "text": arrow_html,
                    "useHTML": True,
                    "backgroundColor": "transparent",
                    "borderWidth": 0,
                    "style": {"color": color, "fontSize": "32px", "fontWeight": "bold"},
                    "padding": 0,
                }
            ],
            "draggable": "",
        }
    )

# Combine all series (no separate legend series - we'll use HTML for legend)
all_series = route_series_list + [station_series]

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

highcharts_annotations_url = "https://code.highcharts.com/modules/annotations.js"
with urllib.request.urlopen(highcharts_annotations_url, timeout=30) as response:
    highcharts_annotations_js = response.read().decode("utf-8")

# Build Highcharts options as JSON
chart_options = {
    "chart": {
        "type": "scatter",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginBottom": 150,
        "spacingBottom": 50,
    },
    "title": {
        "text": "network-transport-static · highcharts · pyplots.ai",
        "style": {"fontSize": "52px", "fontWeight": "bold"},
    },
    "subtitle": {
        "text": 'Regional Rail Network - 12 Stations, 19 Routes<br/><span style="font-size:26px;"><span style="color:#306998;">■</span> Express (EX) &nbsp;&nbsp;&nbsp; <span style="color:#FFD43B;">■</span> Regional (RE) &nbsp;&nbsp;&nbsp; <span style="color:#9467BD;">■</span> Local (LC)</span>',
        "useHTML": True,
        "style": {"fontSize": "32px"},
    },
    "xAxis": {"min": 0, "max": 100, "visible": False, "gridLineWidth": 0},
    "yAxis": {"min": 0, "max": 100, "visible": False, "gridLineWidth": 0, "reversed": True},
    "legend": {"enabled": False},
    "tooltip": {
        "enabled": True,
        "style": {"fontSize": "22px"},
        "headerFormat": "",
        "pointFormat": "<b>{series.name}</b>",
    },
    "plotOptions": {"series": {"animation": False}},
    "series": all_series,
    "annotations": annotations_list,
}

options_json = json.dumps(chart_options)

# Generate HTML with direct Highcharts.chart() call
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{highcharts_annotations_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {options_json});
    </script>
</body>
</html>"""

# Save HTML file
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
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
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
