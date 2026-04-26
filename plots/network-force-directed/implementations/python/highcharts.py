""" anyplot.ai
network-force-directed: Force-Directed Graph
Library: highcharts unknown | Python 3.14.4
Quality: 83/100 | Updated: 2026-04-26
"""

import os
import random
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
LABEL_OUTLINE = PAGE_BG

# Data - Social network with communities
random.seed(42)

# Define nodes: 32 people in 4 communities
communities = {
    "Tech": ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Henry"],
    "Marketing": ["Kate", "Leo", "Mia", "Noah", "Olivia", "Paul", "Quinn", "Rose"],
    "Finance": ["Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier", "Yara", "Zack"],
    "Design": ["Amy", "Ben", "Chloe", "Dan", "Emma", "Finn", "Gina", "Hugo"],
}

# Community colors — Okabe-Ito positions 1-4
community_colors = {"Tech": "#009E73", "Marketing": "#D55E00", "Finance": "#0072B2", "Design": "#CC79A7"}

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

# Create node configurations
node_configs = []
for n in nodes:
    node_configs.append({"id": n["id"], "color": n["color"], "marker": {"radius": 32}})

# Download Highcharts JS and networkgraph module
highcharts_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highcharts.js"
networkgraph_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/modules/networkgraph.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(networkgraph_url, timeout=30) as response:
    networkgraph_js = response.read().decode("utf-8")

# Build chart configuration as raw JavaScript for better control
nodes_js = "[\n"
for n in node_configs:
    nodes_js += f'    {{id: "{n["id"]}", color: "{n["color"]}", marker: {{radius: 32}}}},\n'
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
        backgroundColor: '{PAGE_BG}',
        style: {{color: '{INK}'}}
    }},
    title: {{
        text: 'network-force-directed · highcharts · anyplot.ai',
        style: {{fontSize: '56px', fontWeight: 'bold', color: '{INK}'}}
    }},
    subtitle: {{
        useHTML: true,
        text: '<span style="font-size:32px;color:{INK_SOFT};">Communication ties across four departments — dense within, sparse between</span><br/>'
            + '<span style="font-size:30px;">'
            + '<span style="color:#009E73;">&#9679;</span> <span style="color:{INK};">Tech</span> &nbsp;&nbsp;&nbsp;'
            + '<span style="color:#D55E00;">&#9679;</span> <span style="color:{INK};">Marketing</span> &nbsp;&nbsp;&nbsp;'
            + '<span style="color:#0072B2;">&#9679;</span> <span style="color:{INK};">Finance</span> &nbsp;&nbsp;&nbsp;'
            + '<span style="color:#CC79A7;">&#9679;</span> <span style="color:{INK};">Design</span>'
            + '</span>',
        style: {{fontSize: '32px', color: '{INK_SOFT}'}}
    }},
    legend: {{enabled: false}},
    plotOptions: {{
        networkgraph: {{
            layoutAlgorithm: {{
                enableSimulation: true,
                friction: -0.9,
                linkLength: 650,
                gravitationalConstant: 0.06,
                integration: 'verlet',
                maxIterations: 1500
            }},
            dataLabels: {{
                enabled: true,
                linkFormat: '',
                style: {{
                    fontSize: '26px',
                    fontWeight: 'bold',
                    color: '{INK}',
                    textOutline: '3px {LABEL_OUTLINE}'
                }}
            }},
            link: {{
                width: 4,
                color: '{GRID}'
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
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Save HTML file
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
