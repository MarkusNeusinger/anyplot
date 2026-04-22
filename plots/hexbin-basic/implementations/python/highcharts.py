""" pyplots.ai
hexbin-basic: Basic Hexbin Plot
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-02-21
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - seismic sensor readings: 10,000 measurements across a monitoring grid
np.random.seed(42)
n_points = 10000

# Three activity zones with different intensities
zone_a = np.column_stack([np.random.randn(n_points // 3) * 1.2 + 2, np.random.randn(n_points // 3) * 1.0 + 3])
zone_b = np.column_stack([np.random.randn(n_points // 3) * 1.5 - 1, np.random.randn(n_points // 3) * 1.5 - 1])
zone_c = np.column_stack([np.random.randn(n_points // 3) * 0.8 + 4, np.random.randn(n_points // 3) * 0.9 - 2])
points = np.vstack([zone_a, zone_b, zone_c])

# Hexagonal binning
gridsize = 20
x_min, x_max = points[:, 0].min() - 0.5, points[:, 0].max() + 0.5
y_min, y_max = points[:, 1].min() - 0.5, points[:, 1].max() + 0.5

hex_width = (x_max - x_min) / gridsize
hex_height = hex_width * 2 / np.sqrt(3)
vert_spacing = hex_height * 0.75

hex_bins = {}
for px, py in points:
    row = int((py - y_min) / vert_spacing)
    col_offset = (row % 2) * hex_width * 0.5
    col = int((px - x_min - col_offset) / hex_width)
    hex_bins[(col, row)] = hex_bins.get((col, row), 0) + 1

# Find peak density per zone for annotations
zone_peak_bins = {}
for label, zone_data in [("A", zone_a), ("B", zone_b), ("C", zone_c)]:
    zbins = {}
    for px, py in zone_data:
        row = int((py - y_min) / vert_spacing)
        col_offset = (row % 2) * hex_width * 0.5
        col = int((px - x_min - col_offset) / hex_width)
        zbins[(col, row)] = zbins.get((col, row), 0) + 1
    peak = max(zbins, key=zbins.get)
    zone_peak_bins[label] = {"col": peak[0], "row": peak[1], "count": zbins[peak]}

# Build tilemap data
tilemap_data = [{"x": col, "y": row, "value": count} for (col, row), count in hex_bins.items()]
max_count = max(item["value"] for item in tilemap_data)

# Configure chart using highcharts-core SDK
chart = Chart(container="container")
chart.options = HighchartsOptions()
chart.options.chart = {
    "type": "tilemap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginTop": 160,
    "marginBottom": 240,
    "marginLeft": 200,
    "marginRight": 260,
    "animation": False,
}
chart.options.title = {
    "text": "Seismic Activity Density \u00b7 hexbin-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "500", "color": "#1a1a2e"},
}
chart.options.subtitle = {
    "text": (
        f"Three monitoring zones detected \u2014 peak intensity: "
        f"{zone_peak_bins['C']['count']} events/bin (SE quadrant) \u00b7 "
        f"10,000 readings across {len(hex_bins)} hexagonal bins"
    ),
    "style": {"fontSize": "30px", "color": "#555555"},
}
chart.options.x_axis = {
    "title": {"text": "Longitude Grid (\u00b0E)", "style": {"fontSize": "28px", "color": "#333333"}},
    "labels": {"style": {"fontSize": "20px", "color": "#666666"}},
    "gridLineWidth": 0,
    "lineColor": "#aaaaaa",
    "tickColor": "#aaaaaa",
    "lineWidth": 1,
}
chart.options.y_axis = {
    "title": {"text": "Latitude Grid (\u00b0N)", "style": {"fontSize": "28px", "color": "#333333"}},
    "labels": {"style": {"fontSize": "20px", "color": "#666666"}},
    "gridLineWidth": 0,
    "lineColor": "#aaaaaa",
    "tickColor": "#aaaaaa",
    "lineWidth": 1,
}
chart.options.color_axis = {
    "min": 0,
    "max": int(max_count),
    "stops": [
        [0, "#440154"],
        [0.05, "#482878"],
        [0.15, "#3b528b"],
        [0.35, "#21918c"],
        [0.6, "#5ec962"],
        [1, "#fde725"],
    ],
    "labels": {"style": {"fontSize": "24px", "color": "#333333"}},
}
chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 600,
    "symbolWidth": 40,
    "title": {"text": "Event Count", "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#333333"}},
    "itemStyle": {"fontSize": "24px"},
}
chart.options.tooltip = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.plot_options = {
    "tilemap": {
        "tileShape": "hexagon",
        "colsize": 1,
        "rowsize": 1,
        "animation": False,
        "states": {"hover": {"enabled": False}, "inactive": {"enabled": False}},
    }
}

# Generate chart JS using SDK's to_js_literal()
# Note: tilemap borderWidth/borderColor are not serialized by highcharts-core SDK,
# so those are applied via a post-render update below
chart.options.series = [
    {
        "type": "tilemap",
        "name": "Density",
        "data": tilemap_data,
        "tileShape": "hexagon",
        "dataLabels": {"enabled": False},
    }
]
js_literal = chart.to_js_literal()

# Zone annotation config (applied post-render for module compatibility)
zone_descs = {"A": "Moderate Activity", "B": "Low-Activity Spread", "C": "High-Intensity Hotspot"}
annotation_labels = [
    {
        "point": {"x": zone_peak_bins[z]["col"], "y": zone_peak_bins[z]["row"], "xAxis": 0, "yAxis": 0},
        "text": f"{zone_descs[z]}<br>({zone_peak_bins[z]['count']} events/bin)",
    }
    for z in ["A", "B", "C"]
]
annotation_config = json.dumps(
    {
        "draggable": "",
        "labelOptions": {
            "borderRadius": 8,
            "padding": 12,
            "style": {"fontSize": "24px", "fontWeight": "bold", "color": "#1a1a2e"},
            "backgroundColor": "rgba(255, 255, 255, 0.88)",
            "borderColor": "#444444",
            "borderWidth": 2,
        },
        "labels": annotation_labels,
    }
)

# Tilemap border styling (not serialized by highcharts-core SDK)
border_patch = json.dumps({"borderWidth": 1, "borderColor": "rgba(255,255,255,0.3)"})

# Download Highcharts JS modules (inline for headless Chrome compatibility)
module_urls = {
    "highcharts": "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js",
    "heatmap": "https://cdn.jsdelivr.net/npm/highcharts@11/modules/heatmap.js",
    "tilemap": "https://cdn.jsdelivr.net/npm/highcharts@11/modules/tilemap.js",
    "annotations": "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js",
}
js_modules = {}
for name, url in module_urls.items():
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        js_modules[name] = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_modules["highcharts"]}</script>
    <script>{js_modules["heatmap"]}</script>
    <script>{js_modules["tilemap"]}</script>
    <script>{js_modules["annotations"]}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{js_literal}</script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var chart = Highcharts.charts[0];
            if (chart) {{
                chart.series[0].update({border_patch}, false);
                chart.addAnnotation({annotation_config});
                chart.redraw();
            }}
        }});
    </script>
</body>
</html>"""

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with headless Chrome
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
