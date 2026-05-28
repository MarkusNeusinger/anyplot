""" anyplot.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

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

# Normalize for marker size
max_degree = max(weighted_degree.values())
min_degree = min(weighted_degree.values())

# Create nodes for Highcharts networkgraph
nodes_data = []
for i, dept in enumerate(departments):
    deg = weighted_degree[dept["id"]]
    marker_size = 50 + 70 * (deg - min_degree) / (max_degree - min_degree)
    color = IMPRINT[i % len(IMPRINT)]
    nodes_data.append({"id": dept["id"], "name": dept["name"], "marker": {"radius": int(marker_size)}, "color": color})

# Create links with width based on weight
min_weight = min(w for _, _, w in edges)
max_weight = max(w for _, _, w in edges)

links_data = []
for src, tgt, weight in edges:
    width = 4 + 20 * (weight - min_weight) / (max_weight - min_weight)
    links_data.append({"from": src, "to": tgt, "width": round(width, 1)})

# Convert links and nodes to JSON
links_json = json.dumps(links_data)
nodes_json = json.dumps(nodes_data)

# Download Highcharts JS and networkgraph module from jsdelivr CDN
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
networkgraph_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/modules/networkgraph.js"

req_hc = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_hc, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req_ng = urllib.request.Request(networkgraph_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_ng, timeout=30) as response:
    networkgraph_js = response.read().decode("utf-8")

# Generate HTML with inline scripts and theme-adaptive styling
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{networkgraph_js}</script>
    <style>
        body {{ margin: 0; padding: 0; background: {PAGE_BG}; }}
        #container {{ width: 4800px; height: 2700px; }}
        #legend {{
            position: absolute;
            top: 120px;
            right: 120px;
            background: {ELEVATED_BG};
            border: 2px solid {INK_SOFT};
            border-radius: 12px;
            padding: 30px 40px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        #legend h3 {{
            margin: 0 0 20px 0;
            font-size: 28px;
            color: {INK};
            font-weight: 600;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 16px 0;
            font-size: 18px;
            color: {INK_SOFT};
        }}
        .legend-line {{
            height: 0;
            margin-right: 20px;
            border-top-style: solid;
            border-top-color: {IMPRINT[0]};
        }}
        .legend-line.thin {{ width: 80px; border-top-width: 4px; }}
        .legend-line.medium {{ width: 80px; border-top-width: 14px; }}
        .legend-line.thick {{ width: 80px; border-top-width: 24px; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <div id="legend">
        <h3>Edge Weight</h3>
        <div class="legend-item">
            <div class="legend-line thin"></div>
            <span>{int(min_weight)} publications</span>
        </div>
        <div class="legend-item">
            <div class="legend-line medium"></div>
            <span>~{int((min_weight + max_weight) / 2)} publications</span>
        </div>
        <div class="legend-item">
            <div class="legend-line thick"></div>
            <span>{int(max_weight)} publications</span>
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
                backgroundColor: '{PAGE_BG}',
                marginTop: 120,
                marginBottom: 120,
                marginLeft: 120,
                marginRight: 120,
            }},
            title: {{
                text: 'network-weighted · highcharts · anyplot.ai',
                style: {{ fontSize: '28px', fontWeight: '600', color: '{INK}' }}
            }},
            plotOptions: {{
                networkgraph: {{
                    layoutAlgorithm: {{
                        enableSimulation: true,
                        friction: -0.92,
                        linkLength: 280,
                        gravitationalConstant: 0.08,
                        integration: 'verlet',
                        approximation: 'none',
                        initialPositions: 'circle',
                        maxIterations: 3000,
                        initialPositionRadius: 800
                    }},
                    link: {{
                        color: '{INK_SOFT}'
                    }},
                    dataLabels: {{
                        enabled: true,
                        allowOverlap: false,
                        style: {{
                            fontSize: '22px',
                            fontWeight: '600',
                            color: '{INK}',
                            textOutline: '3px {PAGE_BG}'
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
                    format: '{{point.id}}',
                    style: {{
                        fontSize: '22px',
                        fontWeight: '600',
                        color: '{INK}',
                        textOutline: '3px {PAGE_BG}'
                    }}
                }},
                marker: {{
                    radius: 70
                }}
            }}],
            credits: {{ enabled: false }},
            tooltip: {{
                enabled: true,
                style: {{ fontSize: '18px', color: '{INK}' }},
                backgroundColor: '{ELEVATED_BG}',
                borderColor: '{INK_SOFT}',
                formatter: function() {{
                    if (this.point.isNode) {{
                        return '<b style="color: {INK}">' + this.point.id + '</b>';
                    }}
                    var link = linksData.find(function(l) {{
                        return (l.from === this.point.from && l.to === this.point.to) ||
                               (l.from === this.point.to && l.to === this.point.from);
                    }}, this);
                    if (link) {{
                        return '<span style="color: {INK}">' + this.point.from + ' - ' + this.point.to + ': <b>' + link.width.toFixed(1) + '</b></span>';
                    }}
                    return '<span style="color: {INK}">' + this.point.from + ' - ' + this.point.to + '</span>';
                }}
            }}
        }}, function(chart) {{
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

# Write HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG
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
time.sleep(5)  # Wait for network simulation to settle
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
