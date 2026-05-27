""" anyplot.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: highcharts unknown | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-15
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette for categorical data
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data - Primate phylogenetic tree with branch lengths (MYA - Million Years Ago)
phylo_nodes = {
    "Primates": {"name": "Primates", "rank": "Order", "depth": 0},
    "Hominoidea": {"name": "Hominoidea", "rank": "Superfamily", "depth": 25},
    "Cercopithecoidea": {"name": "Cercopithecoidea", "rank": "Superfamily", "depth": 25},
    "Hominidae": {"name": "Hominidae", "rank": "Family", "depth": 40},
    "Hylobatidae": {"name": "Hylobatidae", "rank": "Family", "depth": 40},
    "Cercopithecidae": {"name": "Cercopithecidae", "rank": "Family", "depth": 40},
    "Hominini": {"name": "Hominini", "rank": "Tribe", "depth": 55},
    "Ponginae": {"name": "Ponginae", "rank": "Subfamily", "depth": 55},
    "Cercopithecinae": {"name": "Cercopithecinae", "rank": "Subfamily", "depth": 55},
    "Colobinae": {"name": "Colobinae", "rank": "Subfamily", "depth": 55},
    "Homo_sapiens": {"name": "Homo sapiens", "rank": "Species", "depth": 75},
    "Pan_troglodytes": {"name": "Pan troglodytes", "rank": "Species", "depth": 75},
    "Pongo_pygmaeus": {"name": "Pongo pygmaeus", "rank": "Species", "depth": 75},
    "Hylobates_lar": {"name": "Hylobates lar", "rank": "Species", "depth": 75},
    "Symphalangus": {"name": "Symphalangus syndactylus", "rank": "Species", "depth": 75},
    "Macaca_mulatta": {"name": "Macaca mulatta", "rank": "Species", "depth": 75},
    "Papio_anubis": {"name": "Papio anubis", "rank": "Species", "depth": 75},
    "Colobus_guereza": {"name": "Colobus guereza", "rank": "Species", "depth": 75},
    "Nasalis_larvatus": {"name": "Nasalis larvatus", "rank": "Species", "depth": 75},
}

phylo_edges = [
    ("Primates", "Hominoidea"),
    ("Primates", "Cercopithecoidea"),
    ("Hominoidea", "Hominidae"),
    ("Hominoidea", "Hylobatidae"),
    ("Cercopithecoidea", "Cercopithecidae"),
    ("Hominidae", "Hominini"),
    ("Hominidae", "Ponginae"),
    ("Cercopithecidae", "Cercopithecinae"),
    ("Cercopithecidae", "Colobinae"),
    ("Hominini", "Homo_sapiens"),
    ("Hominini", "Pan_troglodytes"),
    ("Ponginae", "Pongo_pygmaeus"),
    ("Hylobatidae", "Hylobates_lar"),
    ("Hylobatidae", "Symphalangus"),
    ("Cercopithecinae", "Macaca_mulatta"),
    ("Cercopithecinae", "Papio_anubis"),
    ("Colobinae", "Colobus_guereza"),
    ("Colobinae", "Nasalis_larvatus"),
]

# Assign Y positions to nodes
parents = {e[0] for e in phylo_edges}
leaves = [n for n in phylo_nodes if n not in parents]
leaf_spacing = 100 / (len(leaves) + 1)

for i, leaf in enumerate(leaves):
    phylo_nodes[leaf]["y"] = (i + 1) * leaf_spacing

# Build parent-child map
parent_map = {}
for parent, child in phylo_edges:
    if parent not in parent_map:
        parent_map[parent] = []
    parent_map[parent].append(child)


# Propagate Y positions up (parent = mean of children)
def get_y(node):
    if "y" in phylo_nodes[node]:
        return phylo_nodes[node]["y"]
    child_ys = [get_y(c) for c in parent_map.get(node, [])]
    phylo_nodes[node]["y"] = sum(child_ys) / len(child_ys)
    return phylo_nodes[node]["y"]


for node in phylo_nodes:
    get_y(node)

# Rank color mapping using Okabe-Ito palette
rank_colors = {
    "Order": IMPRINT[0],
    "Superfamily": IMPRINT[1],
    "Family": IMPRINT[2],
    "Tribe": IMPRINT[3],
    "Subfamily": IMPRINT[4],
    "Species": IMPRINT[5],
}

# Generate branch lines
branch_lines = []
for parent, child in phylo_edges:
    p_node = phylo_nodes[parent]
    c_node = phylo_nodes[child]
    branch_lines.append(
        {
            "data": [[p_node["depth"], p_node["y"]], [p_node["depth"], c_node["y"]], [c_node["depth"], c_node["y"]]],
            "color": rank_colors.get(c_node["rank"], INK_SOFT),
        }
    )

# Create node markers
node_points = []
for _node_id, node_data in phylo_nodes.items():
    is_species = node_data["rank"] == "Species"
    node_points.append(
        {
            "x": node_data["depth"],
            "y": node_data["y"],
            "name": node_data["name"],
            "rank": node_data["rank"],
            "marker": {
                "symbol": "circle",
                "radius": 12 if is_species else 10,
                "fillColor": rank_colors.get(node_data["rank"], INK_SOFT),
                "lineWidth": 2,
                "lineColor": PAGE_BG,
            },
            "dataLabels": {
                "enabled": is_species,
                "format": "{point.name}",
                "align": "left",
                "x": 18,
                "style": {"fontSize": "22px", "fontWeight": "normal", "color": INK},
            },
        }
    )

# Build series: one line series per branch
series = []
for i, branch in enumerate(branch_lines):
    series.append(
        {
            "type": "line",
            "name": f"branch_{i}",
            "data": branch["data"],
            "color": branch["color"],
            "lineWidth": 4,
            "marker": {"enabled": False},
            "enableMouseTracking": False,
            "showInLegend": False,
        }
    )

# Add node markers as scatter
series.append(
    {
        "type": "scatter",
        "name": "Nodes",
        "data": node_points,
        "marker": {"radius": 10},
        "tooltip": {"pointFormat": "<b>{point.name}</b><br/>Rank: {point.rank}"},
        "showInLegend": False,
    }
)

# Add legend series for rank colors (invisible data, legend-only)
for rank in ["Order", "Superfamily", "Family", "Tribe", "Subfamily", "Species"]:
    series.append(
        {
            "type": "scatter",
            "name": rank,
            "data": [],
            "marker": {"radius": 8, "fillColor": rank_colors[rank], "lineWidth": 2, "lineColor": PAGE_BG},
            "showInLegend": True,
        }
    )

# Scale bar positioning
scale_bar_x = 50
scale_bar_y = 5
scale_length = 25  # 25 MYA

# Highcharts configuration
chart_config = {
    "chart": {
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginTop": 150,
        "marginBottom": 150,
        "marginLeft": 200,
        "marginRight": 600,
    },
    "title": {
        "text": "tree-phylogenetic · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
    },
    "subtitle": {
        "text": "Primate Evolutionary Relationships · Divergence Times from Mitochondrial DNA",
        "style": {"fontSize": "22px", "color": INK_SOFT},
    },
    "credits": {"enabled": False},
    "legend": {
        "enabled": True,
        "align": "right",
        "layout": "vertical",
        "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "title": {"text": "Taxonomic Rank", "style": {"fontSize": "20px", "color": INK}},
    },
    "xAxis": {
        "title": {"text": "Divergence Time (Million Years Ago)", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "min": -5,
        "max": 85,
        "tickInterval": 10,
        "gridLineWidth": 0,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "reversed": True,
    },
    "yAxis": {
        "title": {"text": ""},
        "labels": {"enabled": False},
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "min": 0,
        "max": 100,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
    },
    "tooltip": {"style": {"fontSize": "18px", "color": INK}},
    "plotOptions": {
        "series": {"animation": False},
        "scatter": {"dataLabels": {"enabled": True, "style": {"fontSize": "22px"}}},
    },
    "annotations": [
        {
            "draggable": "",
            "labelOptions": {"backgroundColor": "transparent", "borderWidth": 0},
            "labels": [
                {
                    "point": {"x": scale_bar_x, "y": scale_bar_y, "xAxis": 0, "yAxis": 0},
                    "text": f'<span style="font-size:20px;color:{INK};">Scale: {scale_length} MYA</span>',
                    "useHTML": True,
                    "y": -40,
                }
            ],
            "shapes": [
                {
                    "type": "path",
                    "points": [
                        {"x": scale_bar_x, "y": scale_bar_y, "xAxis": 0, "yAxis": 0},
                        {"x": scale_bar_x - scale_length, "y": scale_bar_y, "xAxis": 0, "yAxis": 0},
                    ],
                    "stroke": INK_SOFT,
                    "strokeWidth": 6,
                },
                {
                    "type": "path",
                    "points": [
                        {"x": scale_bar_x, "y": scale_bar_y - 1, "xAxis": 0, "yAxis": 0},
                        {"x": scale_bar_x, "y": scale_bar_y + 1, "xAxis": 0, "yAxis": 0},
                    ],
                    "stroke": INK_SOFT,
                    "strokeWidth": 6,
                },
                {
                    "type": "path",
                    "points": [
                        {"x": scale_bar_x - scale_length, "y": scale_bar_y - 1, "xAxis": 0, "yAxis": 0},
                        {"x": scale_bar_x - scale_length, "y": scale_bar_y + 1, "xAxis": 0, "yAxis": 0},
                    ],
                    "stroke": INK_SOFT,
                    "strokeWidth": 6,
                },
            ],
        }
    ],
    "series": series,
}

# Convert config to JSON
config_json = json.dumps(chart_config)

# Download Highcharts JS and required modules
modules = [
    ("highcharts", "https://cdn.jsdelivr.net/npm/highcharts@11.4.0/highcharts.min.js"),
    ("annotations", "https://cdn.jsdelivr.net/npm/highcharts@11.4.0/modules/annotations.min.js"),
]

js_modules = {}
for name, url in modules:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        js_modules[name] = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_modules["highcharts"]}</script>
    <script>{js_modules["annotations"]}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {config_json});
    </script>
</body>
</html>"""

# Save HTML file with theme suffix
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
time.sleep(5)

driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
