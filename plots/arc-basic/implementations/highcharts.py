""" pyplots.ai
arc-basic: Basic Arc Diagram
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 87/100 | Created: 2026-02-23
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Character interactions in a story chapter
nodes = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Iris", "Jack"]

# Edges: (source, target, weight) — dialogue exchange count
edges = [
    ("Alice", "Bob", 5),
    ("Alice", "David", 3),
    ("Bob", "Carol", 3),
    ("Carol", "Eve", 2),
    ("David", "Frank", 3),
    ("Eve", "Grace", 1),
    ("Alice", "Henry", 2),
    ("Bob", "Frank", 3),
    ("Carol", "David", 4),
    ("Frank", "Iris", 1),
    ("Grace", "Jack", 2),
    ("Alice", "Jack", 1),
    ("David", "Henry", 3),
    ("Henry", "Iris", 2),
    ("Iris", "Jack", 3),
]

# Node connection counts for marker sizing
degree = dict.fromkeys(nodes, 0)
for src, tgt, _ in edges:
    degree[src] += 1
    degree[tgt] += 1

# Colorblind-safe palette — Python Blue anchor with complementary tones
node_colors = {
    "Alice": "#306998",
    "Bob": "#E8A317",
    "Carol": "#17BECF",
    "David": "#9467BD",
    "Eve": "#2CA02C",
    "Frank": "#D4652F",
    "Grace": "#8C564B",
    "Henry": "#1F77B4",
    "Iris": "#E377C2",
    "Jack": "#5DA88A",
}

# Node config with degree-scaled markers (3-4x default for 4800x2700)
nodes_data = []
for name in nodes:
    nodes_data.append(
        {
            "id": name,
            "color": node_colors[name],
            "marker": {"radius": 40 + degree[name] * 8, "lineWidth": 4, "lineColor": "#ffffff"},
        }
    )

# Scale weights up for visual node sizing (arc diagram sizes nodes by total weight flow)
weight_scale = 10
links_data = [{"from": src, "to": tgt, "weight": w * weight_scale} for src, tgt, w in edges]

# Chart options (raw JS — highcharts_core doesn't support arcdiagram type)
chart_options = {
    "chart": {
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginTop": 150,
        "marginBottom": 30,
        "marginLeft": 100,
        "marginRight": 100,
        "spacingBottom": 0,
    },
    "title": {
        "text": "Character Interactions \u00b7 arc-basic \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "56px", "fontWeight": "bold", "color": "#333333"},
        "margin": 30,
    },
    "subtitle": {
        "text": "Dialogue exchanges between characters in a story chapter",
        "style": {"fontSize": "36px", "color": "#666666"},
    },
    "accessibility": {"enabled": False},
    "tooltip": {
        "style": {"fontSize": "32px"},
        "nodeFormat": "{point.name}: {point.sum} exchanges",
        "pointFormat": "{point.fromNode.name} \u2192 {point.toNode.name}: {point.weight} exchanges",
    },
    "series": [
        {
            "type": "arcdiagram",
            "name": "Interactions",
            "keys": ["from", "to", "weight"],
            "nodes": nodes_data,
            "data": links_data,
            "colorByPoint": True,
            "centeredLinks": True,
            "linkColorMode": "from",
            "linkOpacity": 0.5,
            "linkWeight": 14,
            "equalNodes": False,
            "nodeWidth": 55,
            "minLinkWidth": 6,
            "marker": {"radius": 50, "lineWidth": 5, "lineColor": "#ffffff"},
            "dataLabels": [
                {
                    "enabled": True,
                    "rotation": 0,
                    "y": 80,
                    "align": "center",
                    "nodeFormat": "{point.name}",
                    "format": "",
                    "linkFormat": "",
                    "style": {
                        "fontSize": "40px",
                        "fontWeight": "bold",
                        "textOutline": "3px #ffffff",
                        "color": "#333333",
                    },
                    "linkTextPath": {"enabled": False},
                }
            ],
        }
    ],
    "legend": {"enabled": False},
    "credits": {"enabled": False},
}

options_json = json.dumps(chart_options)

# Download Highcharts JS, sankey module (dependency), and arc-diagram module
cache_dir = Path("/tmp")
urls = {
    "highcharts": ("https://cdn.jsdelivr.net/npm/highcharts@11.4.8/highcharts.js", cache_dir / "highcharts.js"),
    "sankey": ("https://cdn.jsdelivr.net/npm/highcharts@11.4.8/modules/sankey.js", cache_dir / "hc_sankey.js"),
    "arcdiagram": (
        "https://cdn.jsdelivr.net/npm/highcharts@11.4.8/modules/arc-diagram.js",
        cache_dir / "hc_arc_diagram.js",
    ),
}
js_scripts = {}
for name, (url, cache_path) in urls.items():
    if cache_path.exists() and cache_path.stat().st_size > 1000:
        js_scripts[name] = cache_path.read_text(encoding="utf-8")
    else:
        for attempt in range(5):
            try:
                with urllib.request.urlopen(url, timeout=30) as resp:
                    content = resp.read().decode("utf-8")
                cache_path.write_text(content, encoding="utf-8")
                js_scripts[name] = content
                break
            except urllib.error.HTTPError:
                time.sleep(3 * (attempt + 1))
highcharts_js = js_scripts["highcharts"]
sankey_js = js_scripts["sankey"]
arcdiagram_js = js_scripts["arcdiagram"]

# Post-render JS: remove link labels and enlarge node circles
cleanup_js = """
setTimeout(function() {
    // Remove link labels (internal IDs rendered on arc paths)
    document.querySelectorAll('.highcharts-data-label textPath').forEach(function(el) {
        el.parentNode.parentNode.style.display = 'none';
    });
    document.querySelectorAll('.highcharts-data-label text').forEach(function(el) {
        if (el.textContent && el.textContent.indexOf('highcharts-') === 0) {
            el.parentNode.style.display = 'none';
        }
    });
    // Enlarge node paths (rendered as SVG arcs, not circles) via transform scale
    var chart = Highcharts.charts[0];
    if (chart && chart.series[0] && chart.series[0].nodes) {
        chart.series[0].nodes.forEach(function(node) {
            if (node.graphic) {
                var el = node.graphic.element;
                var bbox = el.getBBox();
                var cx = bbox.x + bbox.width / 2;
                var cy = bbox.y + bbox.height / 2;
                var scale = 2.5;
                el.setAttribute('transform',
                    'translate(' + cx + ',' + cy + ') scale(' + scale + ') translate(' + (-cx) + ',' + (-cy) + ')');
                el.setAttribute('stroke-width', '2');
            }
        });
    }
}, 2500);
"""

# Build HTML with inline JS
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{sankey_js}</script>
    <script>{arcdiagram_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {options_json});
        {cleanup_js}
    </script>
</body>
</html>"""

# Save interactive HTML version (CDN links for standalone use)
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11.4.8/highcharts.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11.4.8/modules/sankey.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11.4.8/modules/arc-diagram.js"></script>
</head>
<body style="margin:0; overflow:auto;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {options_json});
        {cleanup_js}
    </script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
