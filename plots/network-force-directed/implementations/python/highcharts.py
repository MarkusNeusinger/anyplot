""" pyplots.ai
network-force-directed: Force-Directed Graph
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import random
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Social network with communities
random.seed(42)

# Define nodes: 32 people in 4 communities
communities = {
    "Tech": ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Henry"],
    "Marketing": ["Kate", "Leo", "Mia", "Noah", "Olivia", "Paul", "Quinn", "Rose"],
    "Finance": ["Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier", "Yara", "Zack"],
    "Design": ["Amy", "Ben", "Chloe", "Dan", "Emma", "Finn", "Gina", "Hugo"],
}

# Community colors (colorblind-safe)
community_colors = {
    "Tech": "#306998",  # Python Blue
    "Marketing": "#FFD43B",  # Python Yellow
    "Finance": "#9467BD",  # Purple
    "Design": "#17BECF",  # Cyan
}

# Build nodes with community info
nodes = []
node_to_community = {}
for community, members in communities.items():
    for member in members:
        nodes.append({"id": member, "name": member, "color": community_colors[community]})
        node_to_community[member] = community

# Build edges - dense within communities, sparse between
edges = []
added_edges = set()

# Intra-community connections (many)
for _community, members in communities.items():
    for member in members:
        num_connections = random.randint(2, min(4, len(members) - 1))
        others = [m for m in members if m != member]
        targets = random.sample(others, num_connections)
        for target in targets:
            edge = tuple(sorted([member, target]))
            if edge not in added_edges:
                edges.append({"from": member, "to": target})
                added_edges.add(edge)

# Inter-community connections (fewer - bridges between communities)
community_list = list(communities.keys())
for i, comm1 in enumerate(community_list):
    for comm2 in community_list[i + 1 :]:
        num_bridges = random.randint(1, 2)
        for _ in range(num_bridges):
            person1 = random.choice(communities[comm1])
            person2 = random.choice(communities[comm2])
            edge = tuple(sorted([person1, person2]))
            if edge not in added_edges:
                edges.append({"from": person1, "to": person2})
                added_edges.add(edge)

# Prepare series data
series_data = []
for edge in edges:
    series_data.append([edge["from"], edge["to"]])

# Create node configurations with larger markers
node_configs = []
for n in nodes:
    node_configs.append(
        {"id": n["id"], "color": n["color"], "marker": {"radius": 45}, "dataLabels": {"style": {"fontSize": "28px"}}}
    )

# Download Highcharts JS and networkgraph module
highcharts_url = "https://code.highcharts.com/highcharts.js"
networkgraph_url = "https://code.highcharts.com/modules/networkgraph.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(networkgraph_url, timeout=30) as response:
    networkgraph_js = response.read().decode("utf-8")

# Build chart configuration as raw JavaScript for better control
nodes_js = "[\n"
for n in node_configs:
    nodes_js += f'    {{id: "{n["id"]}", color: "{n["color"]}", marker: {{radius: 45}}}},\n'
nodes_js += "]"

data_js = "[\n"
for edge in edges:
    data_js += f'    ["{edge["from"]}", "{edge["to"]}"],\n'
data_js += "]"

chart_js = f"""
Highcharts.chart('container', {{
    chart: {{
        type: 'networkgraph',
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff'
    }},
    title: {{
        text: 'network-force-directed · highcharts · pyplots.ai',
        style: {{fontSize: '56px', fontWeight: 'bold'}}
    }},
    subtitle: {{
        text: 'Social Network with 4 Communities (Tech: Blue, Marketing: Yellow, Finance: Purple, Design: Cyan)',
        style: {{fontSize: '32px', color: '#666666'}}
    }},
    plotOptions: {{
        networkgraph: {{
            layoutAlgorithm: {{
                enableSimulation: true,
                friction: -0.9,
                linkLength: 250,
                gravitationalConstant: 0.02,
                integration: 'verlet',
                maxIterations: 1000
            }},
            dataLabels: {{
                enabled: true,
                linkFormat: '',
                style: {{
                    fontSize: '26px',
                    fontWeight: 'bold',
                    textOutline: '3px white'
                }}
            }},
            link: {{
                width: 4,
                color: '#999999'
            }}
        }}
    }},
    series: [{{
        type: 'networkgraph',
        name: 'Social Network',
        data: {data_js},
        nodes: {nodes_js}
    }}]
}});
"""

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{networkgraph_js}</script>
</head>
<body style="margin:0; padding:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Save HTML file
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
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
time.sleep(12)  # Wait longer for force simulation to stabilize
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
