""" anyplot.ai
network-directed: Directed Network Graph
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-14
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first position for nodes, others for edge variants if needed)
BRAND = "#009E73"  # First series, always
SECONDARY = "#C475FD"  # For arrow highlights if multi-directional

# Data - Software module dependencies showing import direction
nodes = [
    {"id": "main", "name": "main"},
    {"id": "api", "name": "api"},
    {"id": "auth", "name": "auth"},
    {"id": "database", "name": "database"},
    {"id": "models", "name": "models"},
    {"id": "utils", "name": "utils"},
    {"id": "config", "name": "config"},
    {"id": "cache", "name": "cache"},
    {"id": "logging", "name": "logging"},
    {"id": "validation", "name": "validation"},
    {"id": "routes", "name": "routes"},
    {"id": "middleware", "name": "middleware"},
]

# Directed edges (source -> target) showing import dependencies
edges = [
    ("main", "api"),
    ("main", "config"),
    ("main", "logging"),
    ("api", "routes"),
    ("api", "middleware"),
    ("routes", "auth"),
    ("routes", "database"),
    ("routes", "models"),
    ("routes", "validation"),
    ("middleware", "auth"),
    ("middleware", "logging"),
    ("auth", "database"),
    ("auth", "cache"),
    ("auth", "utils"),
    ("database", "models"),
    ("database", "config"),
    ("database", "logging"),
    ("models", "validation"),
    ("cache", "config"),
    ("cache", "logging"),
    ("utils", "config"),
    ("validation", "utils"),
]

# Fixed node positions for reproducibility (arranged in hierarchical layers)
node_positions = {
    "main": (2400, 350),
    "api": (1400, 700),
    "config": (2400, 700),
    "logging": (3400, 700),
    "routes": (1000, 1100),
    "middleware": (1800, 1100),
    "auth": (600, 1550),
    "database": (1400, 1550),
    "models": (2200, 1550),
    "validation": (3400, 1550),
    "cache": (1000, 2000),
    "utils": (3000, 2000),
}

# Format data for Highcharts networkgraph with fixed positions
nodes_data = [{"id": n["id"], "name": n["name"]} for n in nodes]
links_data = [{"from": src, "to": tgt} for src, tgt in edges]

# Download Highcharts JS files
highcharts_url = "https://code.highcharts.com/highcharts.js"
networkgraph_url = "https://code.highcharts.com/modules/networkgraph.js"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.highcharts.com/",
}

req = urllib.request.Request(highcharts_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req = urllib.request.Request(networkgraph_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    networkgraph_js = response.read().decode("utf-8")

# Build data as JSON
nodes_json = json.dumps(nodes_data)
links_json = json.dumps(links_data)
positions_json = json.dumps(node_positions)
edges_json = json.dumps(edges)

# Create HTML with inline scripts - using fixed positions for reproducibility
# Arrows are drawn as separate SVG elements after the chart renders
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{networkgraph_js}</script>
    <style>
        body {{ margin: 0; padding: 0; background: {PAGE_BG}; }}
        #container {{ width: 4800px; height: 2700px; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <script>
        var nodePositions = {positions_json};
        var nodesData = {nodes_json};
        var linksData = {links_json};
        var edgeList = {edges_json};

        var chart = Highcharts.chart('container', {{
            chart: {{
                type: 'networkgraph',
                width: 4800,
                height: 2700,
                backgroundColor: '{PAGE_BG}',
                marginTop: 200,
                marginBottom: 250,
                marginLeft: 350,
                marginRight: 350,
                events: {{
                    load: function() {{
                        var chart = this;
                        var series = chart.series[0];

                        // Set fixed positions for all nodes
                        series.nodes.forEach(function(node) {{
                            var pos = nodePositions[node.id];
                            if (pos) {{
                                node.plotX = pos[0];
                                node.plotY = pos[1];
                                node.fixedPosition = true;
                            }}
                        }});
                        series.isDirty = true;
                        chart.redraw();

                        // Draw arrows after positions are set
                        setTimeout(function() {{
                            drawArrows(chart, series, nodePositions, edgeList);
                        }}, 300);
                    }}
                }}
            }},
            title: {{
                text: 'network-directed · highcharts · anyplot.ai',
                style: {{
                    fontSize: '28px',
                    fontWeight: 'normal',
                    color: '{INK}'
                }}
            }},
            credits: {{
                enabled: false
            }},
            plotOptions: {{
                networkgraph: {{
                    layoutAlgorithm: {{
                        enableSimulation: false,
                        initialPositions: 'circle'
                    }},
                    link: {{
                        width: 3,
                        color: '{INK_SOFT}'
                    }},
                    dataLabels: {{
                        enabled: true,
                        linkFormat: '',
                        style: {{
                            fontSize: '22px',
                            fontWeight: 'normal',
                            color: '{INK}',
                            textOutline: '3px {PAGE_BG}'
                        }}
                    }}
                }}
            }},
            series: [{{
                type: 'networkgraph',
                draggable: false,
                marker: {{
                    radius: 40
                }},
                dataLabels: {{
                    enabled: true,
                    style: {{
                        fontSize: '18px',
                        fontWeight: 'normal',
                        color: '{INK}',
                        textOutline: '3px {PAGE_BG}'
                    }}
                }},
                nodes: nodesData,
                data: linksData,
                color: '{BRAND}'
            }}]
        }});

        // Draw arrow heads at end of each edge
        function drawArrows(chart, series, positions, edges) {{
            var renderer = chart.renderer;
            var nodeRadius = 40;
            var arrowSize = 16;

            edges.forEach(function(edge) {{
                var fromId = edge[0];
                var toId = edge[1];
                var fromPos = positions[fromId];
                var toPos = positions[toId];

                if (!fromPos || !toPos) return;

                // Calculate direction vector
                var dx = toPos[0] - fromPos[0];
                var dy = toPos[1] - fromPos[1];
                var len = Math.sqrt(dx * dx + dy * dy);

                if (len === 0) return;

                // Normalize
                var nx = dx / len;
                var ny = dy / len;

                // Arrow tip position (at edge of target node)
                var tipX = toPos[0] - nx * (nodeRadius + 5);
                var tipY = toPos[1] - ny * (nodeRadius + 5);

                // Arrow base positions (perpendicular to direction)
                var baseX1 = tipX - nx * arrowSize - ny * arrowSize * 0.6;
                var baseY1 = tipY - ny * arrowSize + nx * arrowSize * 0.6;
                var baseX2 = tipX - nx * arrowSize + ny * arrowSize * 0.6;
                var baseY2 = tipY - ny * arrowSize - nx * arrowSize * 0.6;

                // Offset for chart position
                var offsetX = chart.plotLeft;
                var offsetY = chart.plotTop;

                // Draw filled triangle arrow
                renderer.path([
                    'M', tipX + offsetX, tipY + offsetY,
                    'L', baseX1 + offsetX, baseY1 + offsetY,
                    'L', baseX2 + offsetX, baseY2 + offsetY,
                    'Z'
                ])
                .attr({{
                    fill: '{BRAND}',
                    'stroke-width': 0,
                    zIndex: 10
                }})
                .add();
            }});
        }}
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Setup headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

# Take screenshot
driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Also save the interactive HTML version
Path(f"plot-{THEME}.html").write_text(html_content, encoding="utf-8")

# Clean up temp file
Path(temp_path).unlink()
