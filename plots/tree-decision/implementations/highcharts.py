""" pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: highcharts unknown | Python 3.14.3
Quality: 84/100 | Created: 2026-03-06
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Product Launch Decision Tree
# Stage 1: Launch Product vs Keep Current
# If Launch -> Chance: High Demand (0.6) / Low Demand (0.4)
#   High Demand -> $800K
#   Low Demand -> Stage 2 Decision: Discount vs Withdraw
#     Discount -> $200K
#     Withdraw -> -$100K
# If Keep Current -> Chance: Market Grows (0.5) / Market Stable (0.5)
#   Market Grows -> $400K
#   Market Stable -> $250K
#
# EMV rollback:
#   D2: max(200, -100) = $200K (choose Discount, prune Withdraw)
#   C1: 0.6 * 800 + 0.4 * 200 = $560K
#   C2: 0.5 * 400 + 0.5 * 250 = $325K
#   D1: max(560, 325) = $560K (choose Launch, prune Keep Current)

nodes = [
    {"id": "D1", "x": 300, "y": 1150, "type": "decision", "label": "D1", "value": "EMV: $560K"},
    {"id": "C1", "x": 1300, "y": 500, "type": "chance", "label": "C1", "value": "EMV: $560K"},
    {"id": "C2", "x": 1300, "y": 1800, "type": "chance", "label": "C2", "value": "EMV: $325K"},
    {"id": "T1", "x": 2500, "y": 200, "type": "terminal", "label": "T1", "value": "$800K"},
    {"id": "D2", "x": 2500, "y": 800, "type": "decision", "label": "D2", "value": "EMV: $200K"},
    {"id": "T2", "x": 2500, "y": 1500, "type": "terminal", "label": "T2", "value": "$400K"},
    {"id": "T3", "x": 2500, "y": 2100, "type": "terminal", "label": "T3", "value": "$250K"},
    {"id": "T4", "x": 3700, "y": 550, "type": "terminal", "label": "T4", "value": "$200K"},
    {"id": "T5", "x": 3700, "y": 1050, "type": "terminal", "label": "T5", "value": "-$100K"},
]

edges = [
    {"from": "D1", "to": "C1", "label": "Launch Product", "pruned": False},
    {"from": "D1", "to": "C2", "label": "Keep Current", "pruned": True},
    {"from": "C1", "to": "T1", "label": "High Demand (0.6)", "pruned": False},
    {"from": "C1", "to": "D2", "label": "Low Demand (0.4)", "pruned": False},
    {"from": "C2", "to": "T2", "label": "Market Grows (0.5)", "pruned": True},
    {"from": "C2", "to": "T3", "label": "Market Stable (0.5)", "pruned": True},
    {"from": "D2", "to": "T4", "label": "Discount", "pruned": False},
    {"from": "D2", "to": "T5", "label": "Withdraw", "pruned": True},
]

nodes_json = json.dumps(nodes)
edges_json = json.dumps(edges)

# Download Highcharts JS
highcharts_paths = [
    Path(__file__).resolve().parents[3] / "node_modules" / "highcharts" / "highcharts.js",
    Path("node_modules/highcharts/highcharts.js"),
]
highcharts_js = None
for p in highcharts_paths:
    if p.exists():
        highcharts_js = p.read_text(encoding="utf-8")
        break
if highcharts_js is None:
    highcharts_url = "https://code.highcharts.com/highcharts.js"
    req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")

# Build HTML with custom Highcharts renderer drawing
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:#ffffff;">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>
    (function() {{
        var nodes = {nodes_json};
        var edges = {edges_json};

        var nodeMap = {{}};
        nodes.forEach(function(n) {{ nodeMap[n.id] = n; }});

        var chart = Highcharts.chart('container', {{
            chart: {{
                width: 4800,
                height: 2700,
                backgroundColor: '#ffffff',
                events: {{
                    load: function() {{
                        var ren = this.renderer;
                        var offsetX = 350;
                        var offsetY = 220;
                        var nodeSize = 65;

                        // Draw title
                        ren.text(
                            'tree-decision \\u00b7 highcharts \\u00b7 pyplots.ai',
                            2400, 80
                        ).attr({{
                            align: 'center',
                            zIndex: 10
                        }}).css({{
                            fontSize: '56px',
                            fontWeight: '600',
                            color: '#333333',
                            fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
                        }}).add();

                        // Draw subtitle
                        ren.text(
                            'Product Launch Decision Analysis \\u2014 Expected Monetary Value Rollback',
                            2400, 140
                        ).attr({{
                            align: 'center',
                            zIndex: 10
                        }}).css({{
                            fontSize: '32px',
                            fontWeight: '400',
                            color: '#777777',
                            fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
                        }}).add();

                        // Colors
                        var decisionColor = '#306998';
                        var chanceColor = '#E8833A';
                        var terminalColor = '#2A9D8F';
                        var prunedColor = '#BBBBBB';
                        var optimalEdgeColor = '#306998';
                        var prunedEdgeColor = '#CCCCCC';

                        // Draw edges
                        edges.forEach(function(e) {{
                            var fromNode = nodeMap[e.from];
                            var toNode = nodeMap[e.to];
                            var x1 = fromNode.x + offsetX + nodeSize;
                            var y1 = fromNode.y + offsetY;
                            var x2 = toNode.x + offsetX - nodeSize;
                            var y2 = toNode.y + offsetY;

                            if (toNode.type === 'terminal') {{
                                x2 = toNode.x + offsetX - 40;
                            }}

                            var midX = (x1 + x2) / 2;

                            var pathData = [
                                'M', x1, y1,
                                'C', midX, y1, midX, y2, x2, y2
                            ];

                            var edgeColor = e.pruned ? prunedEdgeColor : optimalEdgeColor;
                            var edgeWidth = e.pruned ? 3 : 5;
                            var dashStyle = e.pruned ? 'Dash' : 'Solid';

                            ren.path(pathData).attr({{
                                'stroke': edgeColor,
                                'stroke-width': edgeWidth,
                                'fill': 'none',
                                'stroke-dasharray': e.pruned ? '16,10' : 'none',
                                zIndex: 1
                            }}).add();

                            // Prune mark (double strike)
                            if (e.pruned) {{
                                var pruneX = x1 + (x2 - x1) * 0.35;
                                var pruneY = y1 + (y2 - y1) * 0.25;
                                ren.path([
                                    'M', pruneX - 12, pruneY - 18,
                                    'L', pruneX + 12, pruneY + 18,
                                    'M', pruneX + 4, pruneY - 18,
                                    'L', pruneX + 28, pruneY + 18
                                ]).attr({{
                                    'stroke': '#CC4444',
                                    'stroke-width': 4,
                                    zIndex: 5
                                }}).add();
                            }}

                            // Branch label
                            var labelX = x1 + (x2 - x1) * 0.45;
                            var labelY = y1 + (y2 - y1) * 0.45 - 20;
                            var labelColor = e.pruned ? '#999999' : '#444444';

                            ren.text(e.label, labelX, labelY).attr({{
                                align: 'center',
                                zIndex: 6
                            }}).css({{
                                fontSize: '30px',
                                fontWeight: '600',
                                color: labelColor,
                                fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
                            }}).add();
                        }});

                        // Draw nodes
                        nodes.forEach(function(n) {{
                            var cx = n.x + offsetX;
                            var cy = n.y + offsetY;
                            var isPruned = false;

                            // Check if node is on a pruned path
                            edges.forEach(function(e) {{
                                if (e.to === n.id && e.pruned) isPruned = true;
                            }});

                            if (n.type === 'decision') {{
                                // Square node
                                var fillColor = isPruned ? '#DDDDDD' : decisionColor;
                                ren.rect(cx - nodeSize, cy - nodeSize, nodeSize * 2, nodeSize * 2, 8)
                                    .attr({{
                                        fill: fillColor,
                                        stroke: isPruned ? '#BBBBBB' : '#1F4D6E',
                                        'stroke-width': 4,
                                        zIndex: 3
                                    }}).add();

                            }} else if (n.type === 'chance') {{
                                // Circle node
                                var fillColor = isPruned ? '#DDDDDD' : chanceColor;
                                ren.circle(cx, cy, nodeSize).attr({{
                                    fill: fillColor,
                                    stroke: isPruned ? '#BBBBBB' : '#B85E20',
                                    'stroke-width': 4,
                                    zIndex: 3
                                }}).add();

                            }} else if (n.type === 'terminal') {{
                                // Right-pointing triangle
                                var fillColor = isPruned ? '#DDDDDD' : terminalColor;
                                var triSize = nodeSize * 0.9;
                                var path = [
                                    'M', cx - triSize, cy - triSize,
                                    'L', cx + triSize, cy,
                                    'L', cx - triSize, cy + triSize,
                                    'Z'
                                ];
                                ren.path(path).attr({{
                                    fill: fillColor,
                                    stroke: isPruned ? '#BBBBBB' : '#1E7A6D',
                                    'stroke-width': 4,
                                    zIndex: 3
                                }}).add();
                            }}

                            // EMV / Payoff value label
                            var valueColor = isPruned ? '#999999' : '#222222';
                            var valueY = cy + nodeSize + 40;
                            if (n.type === 'terminal') {{
                                // Show payoff to the right of terminal
                                ren.text(n.value, cx + nodeSize + 20, cy + 8).attr({{
                                    align: 'left',
                                    zIndex: 6
                                }}).css({{
                                    fontSize: '34px',
                                    fontWeight: '700',
                                    color: valueColor,
                                    fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
                                }}).add();
                            }} else {{
                                // Show EMV below decision/chance nodes
                                ren.text(n.value, cx, valueY).attr({{
                                    align: 'center',
                                    zIndex: 6
                                }}).css({{
                                    fontSize: '32px',
                                    fontWeight: '700',
                                    color: valueColor,
                                    fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
                                }}).add();
                            }}
                        }});

                        // Legend
                        var legendX = 3950;
                        var legendY = 1850;
                        var legendSpacing = 75;

                        ren.text('Legend', legendX, legendY - 30).css({{
                            fontSize: '34px',
                            fontWeight: '700',
                            color: '#333333',
                            fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
                        }}).add();

                        // Decision node legend
                        ren.rect(legendX, legendY, 36, 36, 4).attr({{
                            fill: decisionColor, stroke: '#1F4D6E', 'stroke-width': 2, zIndex: 5
                        }}).add();
                        ren.text('Decision Node', legendX + 54, legendY + 26).css({{
                            fontSize: '28px', color: '#444444',
                            fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
                        }}).add();

                        // Chance node legend
                        ren.circle(legendX + 18, legendY + legendSpacing + 18, 18).attr({{
                            fill: chanceColor, stroke: '#B85E20', 'stroke-width': 2, zIndex: 5
                        }}).add();
                        ren.text('Chance Node', legendX + 54, legendY + legendSpacing + 26).css({{
                            fontSize: '28px', color: '#444444',
                            fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
                        }}).add();

                        // Terminal node legend
                        ren.path([
                            'M', legendX, legendY + legendSpacing * 2 + 36,
                            'L', legendX + 36, legendY + legendSpacing * 2 + 18,
                            'L', legendX, legendY + legendSpacing * 2,
                            'Z'
                        ]).attr({{
                            fill: terminalColor, stroke: '#1E7A6D', 'stroke-width': 2, zIndex: 5
                        }}).add();
                        ren.text('Terminal Node (Payoff)', legendX + 54, legendY + legendSpacing * 2 + 26).css({{
                            fontSize: '28px', color: '#444444',
                            fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
                        }}).add();

                        // Optimal path legend
                        ren.path(['M', legendX, legendY + legendSpacing * 3 + 18, 'L', legendX + 36, legendY + legendSpacing * 3 + 18]).attr({{
                            stroke: optimalEdgeColor, 'stroke-width': 5, zIndex: 5
                        }}).add();
                        ren.text('Optimal Path', legendX + 54, legendY + legendSpacing * 3 + 26).css({{
                            fontSize: '28px', color: '#444444',
                            fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
                        }}).add();

                        // Pruned path legend
                        ren.path(['M', legendX, legendY + legendSpacing * 4 + 18, 'L', legendX + 36, legendY + legendSpacing * 4 + 18]).attr({{
                            stroke: prunedEdgeColor, 'stroke-width': 3, 'stroke-dasharray': '12,8', zIndex: 5
                        }}).add();
                        ren.text('Pruned Branch', legendX + 54, legendY + legendSpacing * 4 + 26).css({{
                            fontSize: '28px', color: '#444444',
                            fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
                        }}).add();
                    }}
                }}
            }},
            title: {{ text: null }},
            credits: {{ enabled: false }},
            xAxis: {{ visible: false }},
            yAxis: {{ visible: false }},
            legend: {{ enabled: false }},
            series: [{{ type: 'scatter', data: [] }}]
        }});
    }})();
    </script>
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
