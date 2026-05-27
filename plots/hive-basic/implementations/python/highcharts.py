""" anyplot.ai
hive-basic: Basic Hive Plot
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-07
"""

import math
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: Software module dependency network
# Nodes assigned to 3 axes by module type: Core, Utility, Interface (deterministic data)
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
    # Core to Utility
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

# Hive plot configuration
num_axes = 3
axis_angles = [3 * math.pi / 2, math.pi / 6, 5 * math.pi / 6]  # top, lower-right, lower-left
inner_radius = 300
outer_radius = 1100
center_x = 2400
center_y = 1500

axis_labels = ["Core", "Utility", "Interface"]

# Pre-compute node coordinates
node_lookup = {n["id"]: n for n in nodes}
node_coords = {}
for node in nodes:
    angle = axis_angles[node["axis"]]
    radius = inner_radius + (outer_radius - inner_radius) * node["position"]
    node_coords[node["id"]] = (center_x + radius * math.cos(angle), center_y + radius * math.sin(angle))

# Download Highcharts JS with fallback for restricted networks
highcharts_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11.4.6/highcharts.js",
    "https://code.highcharts.com/highcharts.js",
]
highcharts_js = None

for url in highcharts_urls:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue

if not highcharts_js:
    fallback_path = Path("/tmp/highcharts.js")
    if fallback_path.exists():
        highcharts_js = fallback_path.read_text()
    else:
        msg = "Failed to download Highcharts from any CDN and no fallback available"
        raise RuntimeError(msg) from None

# Build Highcharts renderer commands for the hive plot
renderer_commands = []

# Draw axis lines with labels
for axis_idx in range(num_axes):
    angle = axis_angles[axis_idx]
    x1 = center_x + inner_radius * math.cos(angle)
    y1 = center_y + inner_radius * math.sin(angle)
    x2 = center_x + (outer_radius + 50) * math.cos(angle)
    y2 = center_y + (outer_radius + 50) * math.sin(angle)
    color = IMPRINT[axis_idx]

    renderer_commands.append(
        f"chart.renderer.path(['M', {x1:.0f}, {y1:.0f}, 'L', {x2:.0f}, {y2:.0f}], null)"
        f".attr({{stroke: '{color}', 'stroke-width': 14, 'stroke-linecap': 'round', opacity: 0.8}}).add();"
    )

    label_x = center_x + (outer_radius + 150) * math.cos(angle)
    label_y = center_y + (outer_radius + 150) * math.sin(angle)
    renderer_commands.append(
        f"chart.renderer.text('{axis_labels[axis_idx]}', {label_x:.0f}, {label_y:.0f})"
        f".attr({{align: 'center'}}).css({{fontSize: '48px', fontWeight: 'bold', color: '{color}'}}).add();"
    )

# Draw edges as curved paths
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
    edge_color = IMPRINT[source["axis"]]
    stroke_width = 3 + weight * 2

    renderer_commands.append(
        f"chart.renderer.path(['M', {x1:.0f}, {y1:.0f}, 'Q', {ctrl_x:.0f}, {ctrl_y:.0f}, {x2:.0f}, {y2:.0f}], null)"
        f".attr({{stroke: '{edge_color}', 'stroke-width': {stroke_width}, fill: 'none', opacity: 0.5}}).add();"
    )

# Draw central hub
hub_color = INK_SOFT
renderer_commands.append(
    f"chart.renderer.circle({center_x}, {center_y}, 55).attr({{fill: '{hub_color}', opacity: 0.5}}).add();"
)

# Draw nodes as circles
for node in nodes:
    x, y = node_coords[node["id"]]
    color = IMPRINT[node["axis"]]

    renderer_commands.append(
        f"chart.renderer.circle({x:.0f}, {y:.0f}, 32).attr({{fill: '{color}', stroke: '{PAGE_BG}', 'stroke-width': 5, zIndex: 10}}).add();"
    )

# Draw node labels
for node in nodes:
    x, y = node_coords[node["id"]]
    node_label = node["label"]

    label_offset = 65
    if node["axis"] == 0:
        lx, ly, align = x + label_offset, y + 8, "left"
    elif node["axis"] == 1:
        lx, ly, align = x + label_offset * 0.8, y - label_offset * 0.3, "left"
    else:
        lx, ly, align = x - label_offset * 0.8, y - label_offset * 0.3, "right"

    renderer_commands.append(
        f"chart.renderer.text('{node_label}', {lx:.0f}, {ly:.0f})"
        f".attr({{align: '{align}'}}).css({{fontSize: '36px', fontWeight: '500', color: '{INK}'}}).add();"
    )

renderer_js = "\n        ".join(renderer_commands)

# Build legend items
legend_items = (
    f"""<div style="margin-bottom: 30px; font-size: 36px; font-weight: bold; color: {INK};">Module Types</div>"""
)
for i, label in enumerate(axis_labels):
    legend_items += f"""
            <div style="display: flex; align-items: center; margin-bottom: 24px;">
                <div style="width: 50px; height: 50px; border-radius: 50%; background: {IMPRINT[i]}; margin-right: 24px; border: 3px solid {PAGE_BG}; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"></div>
                <span style="font-size: 34px; color: {INK};">{label}</span>
            </div>"""
legend_items += f"""
            <div style="margin-top: 40px; margin-bottom: 20px; font-size: 36px; font-weight: bold; color: {INK};">Edge Weight</div>
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <div style="width: 60px; height: 5px; background: {INK_SOFT}; margin-right: 20px;"></div>
                <span style="font-size: 30px; color: {INK};">Light (1)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <div style="width: 60px; height: 7px; background: {INK_SOFT}; margin-right: 20px;"></div>
                <span style="font-size: 30px; color: {INK};">Medium (2)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <div style="width: 60px; height: 9px; background: {INK_SOFT}; margin-right: 20px;"></div>
                <span style="font-size: 30px; color: {INK};">Heavy (3)</span>
            </div>"""

# Build HTML with inline Highcharts JS
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; background: {PAGE_BG}; }}
    </style>
</head>
<body>
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <div style="position: absolute; top: 200px; right: 180px; padding: 30px; background: {ELEVATED_BG}; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: 1px solid {INK_SOFT};">
        {legend_items}
    </div>
    <script>
        Highcharts.chart('container', {{
            chart: {{
                type: 'scatter',
                width: 4800,
                height: 2700,
                backgroundColor: '{PAGE_BG}',
                spacingTop: 100,
                spacingRight: 50,
                spacingBottom: 50,
                spacingLeft: 50,
                events: {{
                    load: function() {{
                        var chart = this;
                        {renderer_js}
                    }}
                }}
            }},
            title: {{
                text: 'hive-basic · highcharts · anyplot.ai',
                style: {{ fontSize: '48px', fontWeight: 'bold', color: '{INK}' }},
                y: 80
            }},
            xAxis: {{
                min: 0,
                max: 4800,
                visible: false,
                labels: {{ enabled: false }}
            }},
            yAxis: {{
                min: 0,
                max: 2700,
                visible: false,
                labels: {{ enabled: false }}
            }},
            legend: {{ enabled: false }},
            credits: {{ enabled: false }},
            plotOptions: {{
                scatter: {{
                    enableMouseTracking: false
                }}
            }},
            series: [{{
                type: 'scatter',
                data: []
            }}]
        }});
    </script>
</body>
</html>"""

# Save interactive HTML
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot for PNG using Selenium
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
