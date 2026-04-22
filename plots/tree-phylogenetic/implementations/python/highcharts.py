""" pyplots.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Primate phylogenetic tree with branch lengths (MYA - Million Years Ago)
# Branch lengths represent evolutionary distances
phylo_data = {
    "nodes": {
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
    },
    "edges": [
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
    ],
}


# Calculate Y positions for each node (vertical spacing)
def assign_y_positions(phylo_data):
    """Assign vertical positions to nodes, with leaves evenly spaced."""
    nodes = phylo_data["nodes"]
    edges = phylo_data["edges"]

    # Find leaf nodes (nodes with no children)
    parents = {e[0] for e in edges}
    leaves = [n for n in nodes if n not in parents]

    # Assign Y positions to leaves (evenly spaced)
    leaf_spacing = 100 / (len(leaves) + 1)
    for i, leaf in enumerate(leaves):
        nodes[leaf]["y"] = (i + 1) * leaf_spacing

    # Build parent-child map
    parent_map = {}
    for parent, child in edges:
        if parent not in parent_map:
            parent_map[parent] = []
        parent_map[parent].append(child)

    # Propagate Y positions up (parent = mean of children)
    def get_y(node):
        if "y" in nodes[node]:
            return nodes[node]["y"]
        child_ys = [get_y(c) for c in parent_map.get(node, [])]
        nodes[node]["y"] = sum(child_ys) / len(child_ys)
        return nodes[node]["y"]

    for node in nodes:
        get_y(node)

    return nodes


nodes = assign_y_positions(phylo_data)

# Generate line data for branches (rectangular/cladogram style with proportional lengths)
branch_lines = []
node_points = []

# Colors based on rank
rank_colors = {
    "Order": "#1a365d",
    "Superfamily": "#2c5282",
    "Family": "#3182ce",
    "Tribe": "#63b3ed",
    "Subfamily": "#63b3ed",
    "Species": "#FFD43B",
}

for parent, child in phylo_data["edges"]:
    p_node = nodes[parent]
    c_node = nodes[child]
    # Horizontal line from parent to parent's x at child's y
    branch_lines.append(
        {
            "data": [[p_node["depth"], p_node["y"]], [p_node["depth"], c_node["y"]], [c_node["depth"], c_node["y"]]],
            "color": rank_colors.get(c_node["rank"], "#306998"),
        }
    )

# Create node markers
for _node_id, node_data in nodes.items():
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
                "fillColor": rank_colors.get(node_data["rank"], "#306998"),
                "lineWidth": 2,
                "lineColor": "#ffffff",
            },
            "dataLabels": {
                "enabled": is_species,
                "format": "{point.name}",
                "align": "left",
                "x": 18,
                "style": {"fontSize": "28px", "fontWeight": "normal", "color": "#333333"},
            },
        }
    )

# Build series array - one line series per branch for proper colors
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

# Add scale bar annotation (0-25 MYA scale bar in bottom right area)
scale_bar_x = 50
scale_bar_y = 5
scale_length = 25  # 25 MYA

# Highcharts configuration
chart_config = {
    "chart": {
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginTop": 180,
        "marginBottom": 180,
        "marginLeft": 200,
        "marginRight": 600,
    },
    "title": {
        "text": "Primate Phylogeny · tree-phylogenetic · highcharts · pyplots.ai",
        "style": {"fontSize": "56px", "fontWeight": "bold"},
    },
    "subtitle": {
        "text": "Evolutionary relationships based on mitochondrial DNA divergence times",
        "style": {"fontSize": "36px", "color": "#666666"},
    },
    "credits": {"enabled": False},
    "legend": {"enabled": False},
    "xAxis": {
        "title": {"text": "Divergence Time (Million Years Ago)", "style": {"fontSize": "32px", "fontWeight": "bold"}},
        "labels": {"style": {"fontSize": "26px"}},
        "min": -5,
        "max": 85,
        "tickInterval": 10,
        "gridLineWidth": 1,
        "gridLineColor": "#e0e0e0",
        "reversed": True,  # Root on right, species on left
    },
    "yAxis": {"title": {"text": ""}, "labels": {"enabled": False}, "gridLineWidth": 0, "min": 0, "max": 100},
    "tooltip": {"style": {"fontSize": "28px"}},
    "plotOptions": {
        "series": {"animation": False},
        "scatter": {"dataLabels": {"enabled": True, "style": {"fontSize": "28px", "textOutline": "2px white"}}},
    },
    "annotations": [
        {
            "draggable": "",
            "labelOptions": {"backgroundColor": "transparent", "borderWidth": 0},
            "labels": [
                {
                    "point": {"x": scale_bar_x, "y": scale_bar_y, "xAxis": 0, "yAxis": 0},
                    "text": f'<span style="font-size:26px;font-weight:bold;">Scale: {scale_length} MYA</span>',
                    "useHTML": True,
                    "y": -30,
                }
            ],
            "shapes": [
                {
                    "type": "path",
                    "points": [
                        {"x": scale_bar_x, "y": scale_bar_y, "xAxis": 0, "yAxis": 0},
                        {"x": scale_bar_x - scale_length, "y": scale_bar_y, "xAxis": 0, "yAxis": 0},
                    ],
                    "stroke": "#333333",
                    "strokeWidth": 6,
                },
                {
                    "type": "path",
                    "points": [
                        {"x": scale_bar_x, "y": scale_bar_y - 1, "xAxis": 0, "yAxis": 0},
                        {"x": scale_bar_x, "y": scale_bar_y + 1, "xAxis": 0, "yAxis": 0},
                    ],
                    "stroke": "#333333",
                    "strokeWidth": 6,
                },
                {
                    "type": "path",
                    "points": [
                        {"x": scale_bar_x - scale_length, "y": scale_bar_y - 1, "xAxis": 0, "yAxis": 0},
                        {"x": scale_bar_x - scale_length, "y": scale_bar_y + 1, "xAxis": 0, "yAxis": 0},
                    ],
                    "stroke": "#333333",
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
    ("highcharts", "https://code.highcharts.com/highcharts.js"),
    ("annotations", "https://code.highcharts.com/modules/annotations.js"),
]

js_modules = {}
for name, url in modules:
    with urllib.request.urlopen(url, timeout=30) as response:
        js_modules[name] = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_modules["highcharts"]}</script>
    <script>{js_modules["annotations"]}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {config_json});
    </script>
</body>
</html>"""

# Save HTML file
with open("plot.html", "w", encoding="utf-8") as f:
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
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)

# Get container element and screenshot it
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
