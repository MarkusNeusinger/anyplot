""" pyplots.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2026-01-08
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Research collaboration network between university departments
np.random.seed(42)

# Departments (nodes)
departments = [
    {"id": "CS", "name": "Computer Science"},
    {"id": "MATH", "name": "Mathematics"},
    {"id": "PHYS", "name": "Physics"},
    {"id": "STAT", "name": "Statistics"},
    {"id": "EE", "name": "Electrical Eng."},
    {"id": "ME", "name": "Mechanical Eng."},
    {"id": "BIO", "name": "Biology"},
    {"id": "CHEM", "name": "Chemistry"},
    {"id": "ECON", "name": "Economics"},
    {"id": "PSYCH", "name": "Psychology"},
    {"id": "MED", "name": "Medicine"},
    {"id": "ENV", "name": "Environmental Sci."},
]

# Collaboration edges with weights (number of joint publications)
edges = [
    ("CS", "MATH", 45),
    ("CS", "STAT", 38),
    ("CS", "EE", 52),
    ("CS", "PHYS", 22),
    ("MATH", "STAT", 41),
    ("MATH", "PHYS", 35),
    ("MATH", "ECON", 18),
    ("PHYS", "EE", 28),
    ("PHYS", "CHEM", 25),
    ("STAT", "ECON", 32),
    ("STAT", "PSYCH", 24),
    ("STAT", "BIO", 19),
    ("EE", "ME", 33),
    ("BIO", "CHEM", 47),
    ("BIO", "MED", 55),
    ("CHEM", "ENV", 29),
    ("MED", "PSYCH", 21),
    ("MED", "BIO", 55),
    ("ENV", "BIO", 26),
    ("ECON", "PSYCH", 15),
]

# Calculate weighted degree for node sizing
weighted_degree = {d["id"]: 0 for d in departments}
for src, tgt, w in edges:
    weighted_degree[src] += w
    weighted_degree[tgt] += w

# Normalize for marker size (bigger nodes = more collaborations)
max_degree = max(weighted_degree.values())
min_degree = min(weighted_degree.values())

# Colors for nodes - colorblind-safe palette
colors = [
    "#306998",
    "#FFD43B",
    "#9467BD",
    "#17BECF",
    "#8C564B",
    "#E377C2",
    "#7F7F7F",
    "#BCBD22",
    "#1F77B4",
    "#FF7F0E",
    "#2CA02C",
    "#D62728",
]

# Create nodes for Highcharts networkgraph
nodes_data = []
for i, dept in enumerate(departments):
    deg = weighted_degree[dept["id"]]
    # Scale marker size between 50 and 120 based on weighted degree
    marker_size = 50 + 70 * (deg - min_degree) / (max_degree - min_degree)
    nodes_data.append(
        {"id": dept["id"], "name": dept["name"], "marker": {"radius": marker_size}, "color": colors[i % len(colors)]}
    )

# Create links with width based on weight
# Scale line width between 4 and 24 based on weight
min_weight = min(w for _, _, w in edges)
max_weight = max(w for _, _, w in edges)

links_data = []
for src, tgt, weight in edges:
    width = 4 + 20 * (weight - min_weight) / (max_weight - min_weight)
    links_data.append({"from": src, "to": tgt, "width": round(width, 1)})

# Convert links and nodes to JSON for embedding
links_json = json.dumps(links_data)
nodes_json = json.dumps(nodes_data)

# Download Highcharts JS and networkgraph module
highcharts_url = "https://code.highcharts.com/highcharts.js"
networkgraph_url = "https://code.highcharts.com/modules/networkgraph.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(networkgraph_url, timeout=30) as response:
    networkgraph_js = response.read().decode("utf-8")

# Generate HTML with inline scripts, weight legend, and custom link width rendering
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{networkgraph_js}</script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #container {{ width: 4800px; height: 2700px; }}
        #legend {{
            position: absolute;
            bottom: 120px;
            left: 150px;
            background: rgba(255, 255, 255, 0.95);
            border: 3px solid #306998;
            border-radius: 12px;
            padding: 30px 40px;
            font-family: 'Segoe UI', Arial, sans-serif;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        #legend h3 {{
            margin: 0 0 20px 0;
            font-size: 36px;
            color: #333;
            font-weight: bold;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 16px 0;
            font-size: 28px;
            color: #444;
        }}
        .legend-line {{
            height: 0;
            margin-right: 20px;
            border-top-style: solid;
            border-top-color: #306998;
        }}
        .legend-line.thin {{ width: 80px; border-top-width: 4px; }}
        .legend-line.medium {{ width: 80px; border-top-width: 14px; }}
        .legend-line.thick {{ width: 80px; border-top-width: 24px; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <div id="legend">
        <h3>Edge Weight (Publications)</h3>
        <div class="legend-item">
            <div class="legend-line thin"></div>
            <span>{min_weight} publications</span>
        </div>
        <div class="legend-item">
            <div class="legend-line medium"></div>
            <span>~{(min_weight + max_weight) // 2} publications</span>
        </div>
        <div class="legend-item">
            <div class="legend-line thick"></div>
            <span>{max_weight} publications</span>
        </div>
    </div>
    <script>
        var linksData = {links_json};
        var nodesData = {nodes_json};

        Highcharts.chart('container', {{
            chart: {{
                type: 'networkgraph',
                width: 4800,
                height: 2700,
                backgroundColor: '#ffffff',
                marginTop: 180,
                marginBottom: 200,
                marginLeft: 400,
                marginRight: 400,
                events: {{
                    load: function() {{
                        // Center the network by adjusting plot area
                        var chart = this;
                        chart.plotBackground.attr({{
                            fill: 'none'
                        }});
                    }}
                }}
            }},
            title: {{
                text: 'network-weighted · highcharts · pyplots.ai',
                style: {{ fontSize: '56px', fontWeight: 'bold' }}
            }},
            subtitle: {{
                text: 'University Department Collaboration Network',
                style: {{ fontSize: '36px', color: '#666666' }}
            }},
            plotOptions: {{
                networkgraph: {{
                    layoutAlgorithm: {{
                        enableSimulation: true,
                        friction: -0.92,
                        linkLength: 320,
                        gravitationalConstant: 0.08,
                        integration: 'verlet',
                        approximation: 'none',
                        initialPositions: 'circle',
                        maxIterations: 3000,
                        initialPositionRadius: 800
                    }},
                    link: {{
                        color: '#306998'
                    }},
                    dataLabels: {{
                        enabled: true,
                        linkFormat: '',
                        allowOverlap: false,
                        style: {{
                            fontSize: '36px',
                            fontWeight: 'bold',
                            textOutline: '4px white'
                        }}
                    }}
                }}
            }},
            series: [{{
                type: 'networkgraph',
                name: 'Collaborations',
                nodes: nodesData,
                data: linksData,
                dataLabels: {{
                    enabled: true,
                    linkFormat: '',
                    format: '{{point.id}}',
                    style: {{
                        fontSize: '36px',
                        fontWeight: 'bold',
                        textOutline: '4px white'
                    }}
                }},
                marker: {{
                    radius: 70
                }}
            }}],
            credits: {{ enabled: false }},
            tooltip: {{
                enabled: true,
                style: {{ fontSize: '28px' }},
                formatter: function() {{
                    if (this.point.isNode) {{
                        return '<b>' + this.point.id + '</b>';
                    }}
                    var link = linksData.find(function(l) {{
                        return (l.from === this.point.from && l.to === this.point.to) ||
                               (l.from === this.point.to && l.to === this.point.from);
                    }}, this);
                    if (link) {{
                        return this.point.from + ' - ' + this.point.to + ': <b>' + link.width.toFixed(1) + '</b>';
                    }}
                    return this.point.from + ' - ' + this.point.to;
                }}
            }}
        }}, function(chart) {{
            // After chart renders, update link widths based on data
            setTimeout(function() {{
                chart.series[0].points.forEach(function(point) {{
                    if (!point.isNode && point.graphic) {{
                        var linkData = linksData.find(function(l) {{
                            return (l.from === point.from && l.to === point.to) ||
                                   (l.from === point.to && l.to === point.from);
                        }});
                        if (linkData) {{
                            point.graphic.attr({{
                                'stroke-width': linkData.width
                            }});
                        }}
                    }}
                }});
            }}, 500);
        }});
    </script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save as plot.html for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(10)  # Wait for network simulation to settle
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
