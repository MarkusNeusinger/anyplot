""" anyplot.ai
network-basic: Basic Network Graph
Library: highcharts unknown | Python 3.14.4
Quality: 83/100 | Updated: 2026-04-27
"""

import json
import math
import os
import tempfile
import time
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.networkgraph import NetworkGraphSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette positions 1–4 for the four communities
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data: A small social network with 20 people in 4 communities
nodes = [
    {"id": "Alice", "group": 0},
    {"id": "Bob", "group": 0},
    {"id": "Carol", "group": 0},
    {"id": "David", "group": 0},
    {"id": "Eve", "group": 0},
    {"id": "Frank", "group": 1},
    {"id": "Grace", "group": 1},
    {"id": "Henry", "group": 1},
    {"id": "Ivy", "group": 1},
    {"id": "Jack", "group": 1},
    {"id": "Kate", "group": 2},
    {"id": "Leo", "group": 2},
    {"id": "Mia", "group": 2},
    {"id": "Noah", "group": 2},
    {"id": "Olivia", "group": 2},
    {"id": "Paul", "group": 3},
    {"id": "Quinn", "group": 3},
    {"id": "Ryan", "group": 3},
    {"id": "Sara", "group": 3},
    {"id": "Tom", "group": 3},
]

# Edges: Friendship connections (within and between groups)
edges = [
    # Group 0 internal
    ("Alice", "Bob"),
    ("Alice", "Carol"),
    ("Bob", "Carol"),
    ("Bob", "David"),
    ("Carol", "Eve"),
    ("David", "Eve"),
    # Group 1 internal
    ("Frank", "Grace"),
    ("Frank", "Henry"),
    ("Grace", "Ivy"),
    ("Henry", "Ivy"),
    ("Henry", "Jack"),
    ("Ivy", "Jack"),
    # Group 2 internal
    ("Kate", "Leo"),
    ("Kate", "Mia"),
    ("Leo", "Noah"),
    ("Mia", "Noah"),
    ("Mia", "Olivia"),
    ("Noah", "Olivia"),
    # Group 3 internal
    ("Paul", "Quinn"),
    ("Paul", "Ryan"),
    ("Quinn", "Sara"),
    ("Ryan", "Sara"),
    ("Ryan", "Tom"),
    ("Sara", "Tom"),
    # Cross-group bridges
    ("Alice", "Frank"),
    ("Eve", "Kate"),
    ("Jack", "Paul"),
    ("Olivia", "Tom"),
    ("Carol", "Grace"),
    ("Ivy", "Leo"),
    ("Noah", "Quinn"),
]

# Calculate node degrees for size scaling
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Deterministic circular positions within each group's quadrant
group_centers = [
    (1500, 900),  # Group 0: top-left
    (3100, 900),  # Group 1: top-right
    (1500, 1700),  # Group 2: bottom-left
    (3100, 1700),  # Group 3: bottom-right
]

nodes_config = []
group_indices = {0: 0, 1: 0, 2: 0, 3: 0}
for node in nodes:
    node_id = node["id"]
    group = node["group"]
    color = OKABE_ITO[group]
    radius = 65 + degrees[node_id] * 8
    center_x, center_y = group_centers[group]
    idx = group_indices[group]
    group_indices[group] += 1
    angle = (2 * math.pi * idx) / 5
    init_x = center_x + 300 * math.cos(angle)
    init_y = center_y + 300 * math.sin(angle)
    nodes_config.append(
        {
            "id": node_id,
            "color": color,
            "marker": {"radius": radius, "fillColor": color, "lineWidth": 3, "lineColor": INK_SOFT},
            "plotX": init_x,
            "plotY": init_y,
        }
    )

group_names = ["Community A", "Community B", "Community C", "Community D"]

# Plot
series = NetworkGraphSeries()
series.name = "Network"
series.data = [{"from": src, "to": tgt} for src, tgt in edges]
series.data_labels = {
    "enabled": True,
    "format": "{point.id}",
    "linkFormat": "",
    "style": {"fontSize": "22px", "fontWeight": "bold", "textOutline": f"3px {PAGE_BG}", "color": INK},
    "allowOverlap": True,
}
series.marker = {"radius": 65}
series.layout_algorithm = {
    "enableSimulation": True,
    "linkLength": 380,
    "gravitationalConstant": 0.025,
    "friction": -0.85,
    "initialPositions": "circle",
    "maxIterations": 300,
    "integration": "verlet",
}
series.animation = False
series.link = {"width": 3, "color": INK_SOFT}
series.show_in_legend = False

chart = Chart(container="container")
chart.options = HighchartsOptions()
chart.options.chart = {
    "type": "networkgraph",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "margin": [120, 300, 100, 80],
}
chart.options.title = {
    "text": "network-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold", "color": INK},
}
chart.options.x_axis = {"visible": False}
chart.options.y_axis = {"visible": False}
chart.options.plot_options = {
    "networkgraph": {"keys": ["from", "to"], "marker": {"radius": 65, "lineWidth": 3, "lineColor": INK_SOFT}}
}
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "x": -20,
    "y": 0,
    "itemStyle": {"fontSize": "32px", "fontWeight": "normal", "color": INK_SOFT},
    "itemMarginBottom": 15,
    "symbolRadius": 14,
    "symbolWidth": 28,
    "symbolHeight": 28,
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "padding": 15,
}
chart.add_series(series)

for color, name in zip(OKABE_ITO, group_names, strict=True):
    legend_series = ScatterSeries()
    legend_series.name = name
    legend_series.color = color
    legend_series.data = []
    legend_series.marker = {"symbol": "circle", "radius": 16}
    legend_series.show_in_legend = True
    chart.add_series(legend_series)

# Inject nodes config into JS (highcharts-core doesn't expose nodes property directly)
js_literal = chart.to_js_literal()
nodes_js = json.dumps(nodes_config)
js_literal = js_literal.replace("series: [{", f"series: [{{\n  nodes: {nodes_js},")
# highcharts-core omits linkFormat; inject it to suppress labels on edges
js_literal = js_literal.replace("format: '{point.id}'", "format: '{point.id}', linkFormat: ''")

# Load Highcharts JS from local npm package (CDN blocked in CI; install via: npm install highcharts --prefix /tmp/hc-tmp)
HC_NPM = Path("/tmp/hc-tmp/node_modules/highcharts")
highcharts_js = (HC_NPM / "highcharts.js").read_text(encoding="utf-8")
highcharts_more_js = (HC_NPM / "highcharts-more.js").read_text(encoding="utf-8")
networkgraph_js = (HC_NPM / "modules/networkgraph.js").read_text(encoding="utf-8")

# Center node labels on circle midpoints after the simulation settles.
# node.plotX/plotY are already in SVG coordinate space for networkgraph — no plotLeft/Top offset.
center_labels_js = """
function centerLabels() {
    var chart = Highcharts.charts[0];
    if (!chart || !chart.series || !chart.series[0]) return;
    var series = chart.series[0];
    if (!series.nodes) return;
    series.nodes.forEach(function(node) {
        if (node.dataLabel && typeof node.plotX !== 'undefined') {
            node.dataLabel.attr({ x: node.plotX, y: node.plotY, 'text-anchor': 'middle' });
            var textEl = node.dataLabel.element.querySelector('text');
            if (textEl) {
                textEl.setAttribute('dominant-baseline', 'central');
                textEl.setAttribute('text-anchor', 'middle');
            }
        }
    });
}
[1000, 3000, 5000, 8000, 11000, 14000, 15500].forEach(function(ms) {
    setTimeout(centerLabels, ms);
});
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        .highcharts-data-label text {{
            dominant-baseline: central !important;
            text-anchor: middle !important;
        }}
    </style>
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{networkgraph_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{js_literal}</script>
    <script>{center_labels_js}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
time.sleep(17)  # Allow simulation to settle and all centerLabels() calls to complete
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
