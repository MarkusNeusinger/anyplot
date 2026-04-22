""" pyplots.ai
hive-basic: Basic Hive Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import math
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Software module dependency network
# Nodes assigned to 3 axes by module type: Core, Utility, Interface
nodes = [
    # Core modules (axis 0) - bottom axis
    {"id": "core_main", "axis": 0, "position": 0.95, "label": "Main"},
    {"id": "core_engine", "axis": 0, "position": 0.75, "label": "Engine"},
    {"id": "core_db", "axis": 0, "position": 0.55, "label": "Database"},
    {"id": "core_auth", "axis": 0, "position": 0.35, "label": "Auth"},
    # Utility modules (axis 1) - upper right axis
    {"id": "util_log", "axis": 1, "position": 0.9, "label": "Logger"},
    {"id": "util_config", "axis": 1, "position": 0.7, "label": "Config"},
    {"id": "util_cache", "axis": 1, "position": 0.5, "label": "Cache"},
    {"id": "util_format", "axis": 1, "position": 0.3, "label": "Format"},
    # Interface modules (axis 2) - upper left axis
    {"id": "iface_api", "axis": 2, "position": 0.85, "label": "API"},
    {"id": "iface_web", "axis": 2, "position": 0.65, "label": "Web"},
    {"id": "iface_cli", "axis": 2, "position": 0.45, "label": "CLI"},
    {"id": "iface_ws", "axis": 2, "position": 0.25, "label": "WebSocket"},
]

edges = [
    # Core to Utility (with weights representing dependency strength)
    {"source": "core_main", "target": "util_log", "weight": 3},
    {"source": "core_main", "target": "util_config", "weight": 3},
    {"source": "core_engine", "target": "util_cache", "weight": 2},
    {"source": "core_engine", "target": "util_log", "weight": 2},
    {"source": "core_db", "target": "util_cache", "weight": 3},
    {"source": "core_db", "target": "util_config", "weight": 1},
    {"source": "core_auth", "target": "util_log", "weight": 2},
    # Core to Interface
    {"source": "core_main", "target": "iface_api", "weight": 3},
    {"source": "core_main", "target": "iface_web", "weight": 2},
    {"source": "core_engine", "target": "iface_api", "weight": 2},
    {"source": "core_auth", "target": "iface_api", "weight": 3},
    {"source": "core_auth", "target": "iface_ws", "weight": 2},
    # Utility to Interface
    {"source": "util_log", "target": "iface_api", "weight": 1},
    {"source": "util_config", "target": "iface_web", "weight": 1},
    {"source": "util_cache", "target": "iface_api", "weight": 2},
    {"source": "util_format", "target": "iface_cli", "weight": 1},
]

# Hive plot configuration - scaled to fill more canvas area
num_axes = 3
axis_angles = [3 * math.pi / 2, math.pi / 6, 5 * math.pi / 6]  # top, lower-right, lower-left
inner_radius = 300
outer_radius = 1100
center_x = 2400
center_y = 1500

# Axis colors (colorblind-safe) and labels
axis_colors = ["#306998", "#FFD43B", "#9467BD"]
axis_labels = ["Core", "Utility", "Interface"]

# Create node lookup and pre-compute coordinates inline
node_lookup = {n["id"]: n for n in nodes}
node_coords = {}
for node in nodes:
    angle = axis_angles[node["axis"]]
    radius = inner_radius + (outer_radius - inner_radius) * node["position"]
    node_coords[node["id"]] = (center_x + radius * math.cos(angle), center_y + radius * math.sin(angle))

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Build Highcharts renderer commands for the hive plot
# Using Highcharts.SVGRenderer API to draw custom elements
renderer_commands = []

# Draw axis lines with labels
for axis_idx in range(num_axes):
    angle = axis_angles[axis_idx]
    x1 = center_x + inner_radius * math.cos(angle)
    y1 = center_y + inner_radius * math.sin(angle)
    x2 = center_x + (outer_radius + 50) * math.cos(angle)
    y2 = center_y + (outer_radius + 50) * math.sin(angle)
    color = axis_colors[axis_idx]

    renderer_commands.append(
        f"chart.renderer.path(['M', {x1:.0f}, {y1:.0f}, 'L', {x2:.0f}, {y2:.0f}])"
        f".attr({{stroke: '{color}', 'stroke-width': 14, 'stroke-linecap': 'round', opacity: 0.8}}).add();"
    )

    label_x = center_x + (outer_radius + 150) * math.cos(angle)
    label_y = center_y + (outer_radius + 150) * math.sin(angle)
    renderer_commands.append(
        f"chart.renderer.text('{axis_labels[axis_idx]}', {label_x:.0f}, {label_y:.0f})"
        f".attr({{align: 'center'}}).css({{fontSize: '48px', fontWeight: 'bold', color: '{color}'}}).add();"
    )

# Draw edges as curved paths with weight-based thickness
for edge in edges:
    source_id = edge["source"]
    target_id = edge["target"]
    weight = edge["weight"]
    source = node_lookup[source_id]
    x1, y1 = node_coords[source_id]
    x2, y2 = node_coords[target_id]

    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    ctrl_x = center_x + (mid_x - center_x) * 0.15
    ctrl_y = center_y + (mid_y - center_y) * 0.15
    edge_color = axis_colors[source["axis"]]
    stroke_width = 3 + weight * 2  # Weight 1=5px, 2=7px, 3=9px

    renderer_commands.append(
        f"chart.renderer.path(['M', {x1:.0f}, {y1:.0f}, 'Q', {ctrl_x:.0f}, {ctrl_y:.0f}, {x2:.0f}, {y2:.0f}])"
        f".attr({{stroke: '{edge_color}', 'stroke-width': {stroke_width}, fill: 'none', opacity: 0.5}}).add();"
    )

# Draw central hub
renderer_commands.append(
    f"chart.renderer.circle({center_x}, {center_y}, 55).attr({{fill: '#666666', opacity: 0.5}}).add();"
)

# Draw nodes with tooltips and labels
for node in nodes:
    x, y = node_coords[node["id"]]
    color = axis_colors[node["axis"]]
    node_id = node["id"]
    node_label = node["label"]
    axis_name = axis_labels[node["axis"]]

    # Calculate degree (number of connections) for tooltip
    degree = sum(1 for e in edges if e["source"] == node_id or e["target"] == node_id)

    renderer_commands.append(
        f"chart.renderer.circle({x:.0f}, {y:.0f}, 32).attr({{fill: '{color}', stroke: '#ffffff', 'stroke-width': 5, zIndex: 10}}).add()"
        f".on('mouseover', function() {{ chart.renderer.label('<b>{node_label}</b><br/>Axis: {axis_name}<br/>Connections: {degree}', {x:.0f} + 40, {y:.0f} - 60)"
        f".attr({{fill: 'rgba(255,255,255,0.95)', stroke: '{color}', 'stroke-width': 2, padding: 12, r: 8, zIndex: 100}}).css({{fontSize: '28px', color: '#333'}}).add(); }})"
        f".on('mouseout', function() {{ Highcharts.each(chart.renderer.box.querySelectorAll('.highcharts-label'), function(el) {{ if(el) el.remove(); }}); }});"
    )

    label_offset = 65
    if node["axis"] == 0:
        lx, ly, align = x + label_offset, y + 8, "left"
    elif node["axis"] == 1:
        lx, ly, align = x + label_offset * 0.8, y - label_offset * 0.3, "left"
    else:
        lx, ly, align = x - label_offset * 0.8, y - label_offset * 0.3, "right"

    renderer_commands.append(
        f"chart.renderer.text('{node_label}', {lx:.0f}, {ly:.0f})"
        f".attr({{align: '{align}'}}).css({{fontSize: '36px', fontWeight: '500', color: '#333333'}}).add();"
    )

renderer_js = "\n        ".join(renderer_commands)

# Build legend items with axis labels and edge weight guide
legend_items = (
    """<div style="margin-bottom: 30px; font-size: 36px; font-weight: bold; color: #333;">Module Types</div>"""
)
for i, label in enumerate(axis_labels):
    legend_items += f"""
            <div style="display: flex; align-items: center; margin-bottom: 24px;">
                <div style="width: 50px; height: 50px; border-radius: 50%; background: {axis_colors[i]}; margin-right: 24px; border: 3px solid #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"></div>
                <span style="font-size: 34px;">{label}</span>
            </div>"""
legend_items += """
            <div style="margin-top: 40px; margin-bottom: 20px; font-size: 36px; font-weight: bold; color: #333;">Edge Weight</div>
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <div style="width: 60px; height: 5px; background: #666; margin-right: 20px;"></div>
                <span style="font-size: 30px;">Light (1)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <div style="width: 60px; height: 7px; background: #666; margin-right: 20px;"></div>
                <span style="font-size: 30px;">Medium (2)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <div style="width: 60px; height: 9px; background: #666; margin-right: 20px;"></div>
                <span style="font-size: 30px;">Heavy (3)</span>
            </div>"""

# Build complete HTML using Highcharts chart and renderer API
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; background: #ffffff; }}
    </style>
</head>
<body>
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <div style="position: absolute; top: 200px; right: 180px; padding: 30px; background: rgba(255,255,255,0.95); border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        {legend_items}
    </div>
    <script>
        var chart = Highcharts.chart('container', {{
            chart: {{
                width: 4800,
                height: 2700,
                backgroundColor: '#ffffff',
                events: {{
                    load: function() {{
                        var chart = this;
                        {renderer_js}
                    }}
                }}
            }},
            title: {{
                text: 'hive-basic · highcharts · pyplots.ai',
                style: {{ fontSize: '48px', fontWeight: 'bold', color: '#333333' }},
                y: 80
            }},
            credits: {{ enabled: false }},
            legend: {{ enabled: false }},
            xAxis: {{ visible: false }},
            yAxis: {{ visible: false }},
            series: [{{ type: 'scatter', data: [] }}]
        }});
    </script>
</body>
</html>"""

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot for PNG
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
