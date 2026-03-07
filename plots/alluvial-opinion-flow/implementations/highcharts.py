""" pyplots.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: highcharts unknown | Python 3.14.3
Quality: 90/100 | Created: 2026-03-03
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Employee satisfaction survey tracking ~1000 employees across 4 quarterly waves
# Categories: Strongly Agree, Agree, Neutral, Disagree, Strongly Disagree
# Topic: "Should the company expand its professional development program?"

waves = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]

# Flow data: [from_node, to_node, flow_count]
# Naming convention: "{Category}_{WaveIndex}" for column positioning
flows = [
    # Q1 -> Q2: After initial program improvements announced
    ["Strongly Agree_0", "Strongly Agree_1", 145],
    ["Strongly Agree_0", "Agree_1", 30],
    ["Strongly Agree_0", "Neutral_1", 5],
    ["Agree_0", "Strongly Agree_1", 25],
    ["Agree_0", "Agree_1", 185],
    ["Agree_0", "Neutral_1", 35],
    ["Agree_0", "Disagree_1", 5],
    ["Neutral_0", "Strongly Agree_1", 5],
    ["Neutral_0", "Agree_1", 30],
    ["Neutral_0", "Neutral_1", 120],
    ["Neutral_0", "Disagree_1", 25],
    ["Neutral_0", "Strongly Disagree_1", 5],
    ["Disagree_0", "Agree_1", 10],
    ["Disagree_0", "Neutral_1", 20],
    ["Disagree_0", "Disagree_1", 115],
    ["Disagree_0", "Strongly Disagree_1", 15],
    ["Strongly Disagree_0", "Neutral_1", 5],
    ["Strongly Disagree_0", "Disagree_1", 15],
    ["Strongly Disagree_0", "Strongly Disagree_1", 100],
    # Q2 -> Q3: After new mentorship program launches
    ["Strongly Agree_1", "Strongly Agree_2", 150],
    ["Strongly Agree_1", "Agree_2", 20],
    ["Strongly Agree_1", "Neutral_2", 5],
    ["Agree_1", "Strongly Agree_2", 35],
    ["Agree_1", "Agree_2", 195],
    ["Agree_1", "Neutral_2", 20],
    ["Agree_1", "Disagree_2", 5],
    ["Neutral_1", "Strongly Agree_2", 5],
    ["Neutral_1", "Agree_2", 40],
    ["Neutral_1", "Neutral_2", 110],
    ["Neutral_1", "Disagree_2", 25],
    ["Neutral_1", "Strongly Disagree_2", 5],
    ["Disagree_1", "Agree_2", 10],
    ["Disagree_1", "Neutral_2", 25],
    ["Disagree_1", "Disagree_2", 105],
    ["Disagree_1", "Strongly Disagree_2", 20],
    ["Strongly Disagree_1", "Neutral_2", 5],
    ["Strongly Disagree_1", "Disagree_2", 10],
    ["Strongly Disagree_1", "Strongly Disagree_2", 105],
    # Q3 -> Q4: After satisfaction results shared
    ["Strongly Agree_2", "Strongly Agree_3", 165],
    ["Strongly Agree_2", "Agree_3", 20],
    ["Strongly Agree_2", "Neutral_3", 5],
    ["Agree_2", "Strongly Agree_3", 40],
    ["Agree_2", "Agree_3", 200],
    ["Agree_2", "Neutral_3", 20],
    ["Agree_2", "Disagree_3", 5],
    ["Neutral_2", "Strongly Agree_3", 5],
    ["Neutral_2", "Agree_3", 35],
    ["Neutral_2", "Neutral_3", 95],
    ["Neutral_2", "Disagree_3", 25],
    ["Neutral_2", "Strongly Disagree_3", 10],
    ["Disagree_2", "Agree_3", 10],
    ["Disagree_2", "Neutral_3", 15],
    ["Disagree_2", "Disagree_3", 100],
    ["Disagree_2", "Strongly Disagree_3", 20],
    ["Strongly Disagree_2", "Neutral_3", 5],
    ["Strongly Disagree_2", "Disagree_3", 10],
    ["Strongly Disagree_2", "Strongly Disagree_3", 115],
]

# Colorblind-safe diverging palette (blue to red via gray)
# Blue-red is robust for deuteranopia and protanopia unlike the previous green-based palette
category_colors = {
    "Strongly Agree": "#2166AC",
    "Agree": "#67A9CF",
    "Neutral": "#878787",
    "Disagree": "#EF8A62",
    "Strongly Disagree": "#B2182B",
}

# Calculate totals per node for labels
node_outgoing = {}
node_incoming = {}
for source, target, count in flows:
    node_outgoing[source] = node_outgoing.get(source, 0) + count
    node_incoming[target] = node_incoming.get(target, 0) + count

# Create nodes with column positions
nodes_data = []
for wave_idx in range(len(waves)):
    for cat in categories:
        node_id = f"{cat}_{wave_idx}"
        # Use outgoing total for first wave, incoming total for subsequent waves
        if wave_idx == 0:
            total = node_outgoing.get(node_id, 0)
        else:
            total = node_incoming.get(node_id, 0)
        nodes_data.append(
            {"id": node_id, "name": f"{cat} ({total})", "column": wave_idx, "color": category_colors[cat]}
        )

# Per-link rgba colors: stable flows (same category) are prominent, changers are faint
# This replaces the global linkOpacity which overrode per-link values
links_data = []
for source, target, weight in flows:
    source_cat = source.rsplit("_", 1)[0]
    target_cat = target.rsplit("_", 1)[0]
    is_stable = source_cat == target_cat
    hex_col = category_colors[source_cat]
    r, g, b = int(hex_col[1:3], 16), int(hex_col[3:5], 16), int(hex_col[5:7], 16)
    alpha = 0.7 if is_stable else 0.15
    links_data.append({"from": source, "to": target, "weight": weight, "color": f"rgba({r},{g},{b},{alpha})"})

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "sankey",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#FAFAFA",
    "marginLeft": 250,
    "marginRight": 700,
    "marginTop": 220,
    "marginBottom": 220,
}

chart.options.title = {
    "text": "Employee Training Satisfaction · alluvial-opinion-flow · highcharts · pyplots.ai",
    "style": {"fontSize": "52px", "fontWeight": "bold", "color": "#2C3E50", "fontFamily": "Georgia, serif"},
}

chart.options.subtitle = {
    "text": ('"Should the company expand its professional development program?" — 1,000 employees tracked quarterly'),
    "style": {"fontSize": "36px", "color": "#5D6D7E", "fontFamily": "Georgia, serif"},
}

chart.options.tooltip = {
    "style": {"fontSize": "32px"},
    "nodeFormat": "{point.name}: {point.sum} respondents",
    "pointFormat": "{point.fromNode.name} → {point.toNode.name}: {point.weight} respondents",
}

series_config = {
    "type": "sankey",
    "name": "Opinion Flow",
    "keys": ["from", "to", "weight"],
    "nodes": nodes_data,
    "data": links_data,
    "dataLabels": {
        "enabled": True,
        "crop": False,
        "overflow": "allow",
        "style": {
            "fontSize": "30px",
            "fontWeight": "bold",
            "color": "#1A1A1A",
            "textOutline": "5px #ffffff",
            "fontFamily": "Arial, sans-serif",
        },
        "nodeFormat": "{point.name}",
    },
    "nodeWidth": 50,
    "nodePadding": 45,
    "linkOpacity": 1,
    "curveFactor": 0.5,
    "colorByPoint": True,
}

chart.options.series = [series_config]

# Wave labels via annotations (x-axis doesn't work with sankey)
wave_x_positions = [280, 1500, 2700, 3850]
chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": wave_x_positions[i], "y": 2480},
                "text": wave,
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "style": {"fontSize": "44px", "fontWeight": "bold", "color": "#2C3E50", "fontFamily": "Georgia, serif"},
            }
            for i, wave in enumerate(waves)
        ],
        "labelOptions": {"useHTML": True},
    }
]

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

# Load Highcharts JS, sankey module, and annotations module
js_local_paths = {
    "highcharts": ["/tmp/hc/node_modules/highcharts/highcharts.js"],
    "sankey": ["/tmp/hc/node_modules/highcharts/modules/sankey.js"],
    "annotations": ["/tmp/hc/node_modules/highcharts/modules/annotations.js"],
}
js_cdn_urls = {
    "highcharts": "https://code.highcharts.com/highcharts.js",
    "sankey": "https://code.highcharts.com/modules/sankey.js",
    "annotations": "https://code.highcharts.com/modules/annotations.js",
}
js_modules = {}
for name in js_cdn_urls:
    loaded = False
    for local_path in js_local_paths.get(name, []):
        if Path(local_path).exists():
            js_modules[name] = Path(local_path).read_text(encoding="utf-8")
            loaded = True
            break
    if not loaded:
        req = urllib.request.Request(js_cdn_urls[name], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            js_modules[name] = response.read().decode("utf-8")

# Generate chart JS
html_str = chart.to_js_literal()

# Custom legend HTML showing opinion categories and stable vs changer distinction
legend_html = """
<div id="custom-legend" style="position: absolute; bottom: 50px; left: 50%; transform: translateX(-50%);
     display: flex; gap: 50px; font-family: Georgia, serif; font-size: 32px; color: #2C3E50;
     align-items: center; flex-wrap: wrap; justify-content: center;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 36px; height: 24px; background-color: #2166AC; border-radius: 4px;"></div>
        <span>Strongly Agree</span>
    </div>
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 36px; height: 24px; background-color: #67A9CF; border-radius: 4px;"></div>
        <span>Agree</span>
    </div>
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 36px; height: 24px; background-color: #878787; border-radius: 4px;"></div>
        <span>Neutral</span>
    </div>
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 36px; height: 24px; background-color: #EF8A62; border-radius: 4px;"></div>
        <span>Disagree</span>
    </div>
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 36px; height: 24px; background-color: #B2182B; border-radius: 4px;"></div>
        <span>Strongly Disagree</span>
    </div>
    <span style="margin-left: 30px; border-left: 2px solid #ccc; padding-left: 30px;">
        Bold flow = stable opinion &nbsp;|&nbsp; Faint flow = opinion changed
    </span>
</div>
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_modules["highcharts"]}</script>
    <script>{js_modules["sankey"]}</script>
    <script>{js_modules["annotations"]}</script>
</head>
<body style="margin:0; position: relative; background-color: #FAFAFA;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    {legend_html}
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive version (use CDN for standalone)
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/sankey.js"></script>
    <script src="https://code.highcharts.com/modules/annotations.js"></script>
</head>
<body style="margin:0; overflow:auto; position: relative; background-color: #FAFAFA;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    {legend_html}
    <script>{html_str}</script>
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
time.sleep(5)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
