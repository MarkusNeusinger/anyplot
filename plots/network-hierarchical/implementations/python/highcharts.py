""" anyplot.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-17
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series is always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Build hierarchical data using Sankey diagram (alternative to organization chart)
# Nodes for each level
ceo = "CEO"
vps = ["VP Engineering", "VP Sales", "VP Operations"]
directors = {
    "VP Engineering": ["Dir Frontend", "Dir Backend", "Dir DevOps"],
    "VP Sales": ["Dir Americas", "Dir EMEA"],
    "VP Operations": ["Dir Logistics", "Dir HR"],
}
managers = {
    "Dir Frontend": ["Mgr React", "Mgr Vue"],
    "Dir Backend": ["Mgr API", "Mgr Database"],
    "Dir DevOps": ["Mgr Cloud"],
    "Dir Americas": ["Mgr NA Sales", "Mgr LATAM"],
    "Dir EMEA": ["Mgr UK Sales", "Mgr DE Sales"],
    "Dir Logistics": ["Mgr Supply"],
    "Dir HR": ["Mgr Talent"],
}

# Build nodes list with colors by level
nodes_list = [ceo]
node_colors = [IMPRINT[0]]  # CEO is level 0

for vp in vps:
    nodes_list.append(vp)
    node_colors.append(IMPRINT[1])

for vp in vps:
    for director in directors[vp]:
        if director not in nodes_list:
            nodes_list.append(director)
            node_colors.append(IMPRINT[2])

for directors_group in managers.values():
    for mgr in directors_group:
        if mgr not in nodes_list:
            nodes_list.append(mgr)
            node_colors.append(IMPRINT[3])

# Build links (from-to pairs with equal weight)
links_list = []
# CEO to VPs
for vp in vps:
    idx_from = nodes_list.index(ceo)
    idx_to = nodes_list.index(vp)
    links_list.append([idx_from, idx_to, 1])

# VPs to Directors
for vp, dirs in directors.items():
    idx_from = nodes_list.index(vp)
    for director in dirs:
        idx_to = nodes_list.index(director)
        links_list.append([idx_from, idx_to, 1])

# Directors to Managers
for director, mgrs in managers.items():
    idx_from = nodes_list.index(director)
    for manager in mgrs:
        idx_to = nodes_list.index(manager)
        links_list.append([idx_from, idx_to, 1])

# Format nodes for JavaScript
nodes_js = "["
for i, node_name in enumerate(nodes_list):
    color = node_colors[i]
    nodes_js += f'{{"name": "{node_name}", "color": "{color}"}}'
    if i < len(nodes_list) - 1:
        nodes_js += ", "
nodes_js += "]"

# Format links for JavaScript
links_js = "["
for i, link in enumerate(links_list):
    links_js += f"[{link[0]}, {link[1]}, {link[2]}]"
    if i < len(links_list) - 1:
        links_js += ", "
links_js += "]"

# Download Highcharts JS from jsDelivr (sankey is in core)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11.4.8/highcharts.js"
sankey_url = "https://cdn.jsdelivr.net/npm/highcharts@11.4.8/modules/sankey.js"

req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req = urllib.request.Request(sankey_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    sankey_js = response.read().decode("utf-8")

# Create Sankey chart configuration
chart_config = f"""
Highcharts.chart('container', {{
    chart: {{
        type: 'sankey',
        width: 4800,
        height: 2700,
        backgroundColor: '{PAGE_BG}'
    }},
    title: {{
        text: 'network-hierarchical · highcharts · anyplot.ai',
        style: {{fontSize: '28px', fontWeight: 'bold', color: '{INK}'}}
    }},
    subtitle: {{
        text: 'Organizational Hierarchy: 22 nodes across 4 levels',
        style: {{fontSize: '22px', color: '{INK_SOFT}'}}
    }},
    credits: {{
        enabled: false
    }},
    legend: {{
        enabled: false
    }},
    plotOptions: {{
        sankey: {{
            nodeWidth: 250,
            nodeHeight: 40,
            dataLabels: {{
                enabled: true,
                style: {{
                    fontSize: '20px',
                    fontWeight: 'bold',
                    color: '{INK}'
                }},
                overflow: 'justify'
            }},
            tooltip: {{
                headerFormat: '<span style="font-size: 18px"><b>{{point.name}}</b></span><br/>',
                pointFormat: '{{}}'
            }}
        }}
    }},
    series: [{{
        type: 'sankey',
        name: 'Organization',
        nodes: {nodes_js},
        data: {links_js},
        colorByPoint: true
    }}]
}});
"""

# Generate HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>network-hierarchical</title>
    <script>{highcharts_js}</script>
    <script>{sankey_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_config}</script>
</body>
</html>"""

# Save HTML
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
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
time.sleep(15)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
