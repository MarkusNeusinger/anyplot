"""anyplot.ai
arc-basic: Basic Arc Diagram
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-05-30
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — 8 hues, canonical order, theme-independent
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data: Character interactions in a story chapter
nodes = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry"]

# Edges: (source, target, weight) — dialogue exchange count
edges = [
    ("Alice", "Bob", 5),
    ("Alice", "David", 3),
    ("Alice", "Grace", 2),
    ("Bob", "Carol", 3),
    ("Bob", "Frank", 3),
    ("Carol", "Eve", 2),
    ("Carol", "David", 4),
    ("David", "Frank", 3),
    ("Eve", "Grace", 1),
    ("Frank", "Henry", 3),
    ("Grace", "Henry", 2),
    ("Alice", "Henry", 2),
    ("David", "Henry", 3),
    ("Eve", "Henry", 1),
]

# Node connection counts for degree-scaled marker sizing
degree = dict.fromkeys(nodes, 0)
for src, tgt, _ in edges:
    degree[src] += 1
    degree[tgt] += 1

# Node config: Imprint palette position per character, degree-scaled radius
nodes_data = []
for i, name in enumerate(nodes):
    nodes_data.append(
        {
            "id": name,
            "color": IMPRINT_PALETTE[i],
            "marker": {"radius": 35 + degree[name] * 8, "lineWidth": 4, "lineColor": PAGE_BG},
        }
    )

# Scale weights for arc visual thickness
links_data = [{"from": src, "to": tgt, "weight": w * 7} for src, tgt, w in edges]

# Title with dynamic fontsize scaling (67-char baseline for 3200×1800)
title = "arc-basic · python · highcharts · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = f"{max(44, round(66 * ratio))}px"

chart_options = {
    "chart": {
        "width": 3200,
        "height": 1800,
        "backgroundColor": PAGE_BG,
        "marginTop": 130,
        "marginBottom": 20,
        "marginLeft": 120,
        "marginRight": 120,
    },
    "title": {"text": title, "style": {"fontSize": title_fontsize, "fontWeight": "bold", "color": INK}, "margin": 20},
    "subtitle": {
        "text": "Dialogue exchanges between characters in a story chapter",
        "style": {"fontSize": "40px", "color": INK_SOFT},
    },
    "accessibility": {"enabled": False},
    "tooltip": {
        "style": {"fontSize": "28px"},
        "nodeFormat": "{point.name}: {point.sum} dialogue exchanges",
        "pointFormat": "{point.fromNode.name} → {point.toNode.name}: {point.weight} exchanges",
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
            "minLinkWidth": 3,
            "equalNodes": False,
            "nodeWidth": 55,
            "dataLabels": [
                {
                    "enabled": True,
                    "rotation": 0,
                    "y": 48,
                    "align": "center",
                    "style": {"fontSize": "44px", "fontWeight": "bold", "textOutline": f"3px {PAGE_BG}", "color": INK},
                }
            ],
        }
    ],
    "legend": {"enabled": False},
    "credits": {"enabled": False},
}

options_json = json.dumps(chart_options)

# Download Highcharts JS modules — arcdiagram requires sankey as a dependency
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

# Use JS formatter to show node names only (not link labels)
chart_init_js = f"""
(function() {{
    var opts = {options_json};
    opts.series[0].dataLabels[0].formatter = function() {{
        return this.point.isNode ? this.point.name : '';
    }};
    Highcharts.chart('container', opts);
}})();
"""

# Build HTML with inline JS (CDN fails under file:// in headless Chrome)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_scripts["highcharts"]}</script>
    <script>{js_scripts["sankey"]}</script>
    <script>{js_scripts["arcdiagram"]}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{chart_init_js}</script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML, take screenshot with CDP viewport override for exact dimensions
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
# CDP override is authoritative — --window-size alone loses ~139 px to Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Normalize to exact 3200×1800 — guards against ±1–2 px rounding in headless Chrome
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
