""" pyplots.ai
network-directed: Directed Network Graph
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2025-12-30
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


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
# Spread nodes more to fill canvas better
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

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(networkgraph_url, timeout=30) as response:
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
        body {{ margin: 0; padding: 0; }}
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
                backgroundColor: '#ffffff',
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
                text: 'network-directed · highcharts · pyplots.ai',
                style: {{
                    fontSize: '56px',
                    fontWeight: 'bold'
                }}
            }},
            subtitle: {{
                text: 'Software Module Dependencies (arrows show import direction)',
                style: {{
                    fontSize: '36px'
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
                        width: 6,
                        color: '#306998'
                    }},
                    dataLabels: {{
                        enabled: true,
                        linkFormat: '',
                        style: {{
                            fontSize: '32px',
                            fontWeight: 'bold',
                            textOutline: '4px white'
                        }}
                    }}
                }}
            }},
            series: [{{
                type: 'networkgraph',
                draggable: false,
                marker: {{
                    radius: 50
                }},
                dataLabels: {{
                    enabled: true,
                    style: {{
                        fontSize: '32px',
                        fontWeight: 'bold',
                        textOutline: '4px white'
                    }}
                }},
                nodes: nodesData,
                data: linksData,
                color: '#FFD43B'
            }}]
        }});

        // Draw arrow heads at end of each edge
        function drawArrows(chart, series, positions, edges) {{
            var renderer = chart.renderer;
            var nodeRadius = 50;
            var arrowSize = 20;

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
                    fill: '#306998',
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
driver.save_screenshot("plot.png")
driver.quit()

# Also save the interactive HTML version
Path("plot.html").write_text(html_content, encoding="utf-8")

# Clean up temp file
Path(temp_path).unlink()
