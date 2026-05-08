"""anyplot.ai
heatmap-adjacency: Network Adjacency Matrix Heatmap
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-05-08
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
EMPTY_CELL = "#E0DFD6" if THEME == "light" else "#2A2A26"

# Data: scientific collaboration network — 25 researchers across 5 departments
np.random.seed(42)

dept_abbrevs = ["NS", "CS", "ST", "GE", "PH"]
dept_names = ["Neurosci", "CompSci", "Statistics", "Genomics", "Physics"]

nodes = [f"{abbr}-{i + 1:02d}" for abbr in dept_abbrevs for i in range(5)]
node_dept = {f"{abbr}-{i + 1:02d}": dept for abbr, dept in zip(dept_abbrevs, dept_names, strict=True) for i in range(5)}

n = len(nodes)
W = np.zeros((n, n))
for i in range(n):
    for j in range(i + 1, n):
        same = node_dept[nodes[i]] == node_dept[nodes[j]]
        if same:
            w = np.random.uniform(0.5, 1.0) if np.random.random() > 0.15 else 0.0
        else:
            w = np.random.uniform(0.1, 0.5) if np.random.random() > 0.80 else 0.0
        W[i, j] = W[j, i] = round(w, 3)

heatmap_data = [[j, i, float(W[i, j])] for i in range(n) for j in range(n)]

# Viridis-like color stops: 0 = distinct empty cell, then viridis from min connection
color_stops = [
    [0.0, EMPTY_CELL],
    [0.1, "#440154"],
    [0.35, "#3b528b"],
    [0.6, "#21908c"],
    [0.8, "#5dc963"],
    [1.0, "#fde725"],
]

# Chart options
options = {
    "chart": {
        "type": "heatmap",
        "width": 3600,
        "height": 3600,
        "backgroundColor": PAGE_BG,
        "marginTop": 160,
        "marginRight": 300,
        "marginBottom": 260,
        "marginLeft": 110,
        "style": {"fontFamily": "sans-serif"},
    },
    "title": {
        "text": "Research Collaboration Network · heatmap-adjacency · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "color": INK, "fontWeight": "600"},
    },
    "subtitle": {
        "text": "25 researchers in 5 departments (NS · CS · ST · GE · PH) — ordered by department to expose block-diagonal structure",
        "style": {"fontSize": "18px", "color": INK_SOFT},
    },
    "xAxis": {
        "categories": nodes,
        "title": {"text": "Researcher", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "16px", "color": INK_SOFT}, "rotation": -45},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
    },
    "yAxis": {
        "categories": nodes,
        "reversed": True,
        "title": {"text": "Researcher", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "16px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
    },
    "colorAxis": {
        "min": 0,
        "max": 1,
        "stops": color_stops,
        "labels": {"style": {"fontSize": "16px", "color": INK_SOFT}},
        "title": {"text": "Collaboration Strength", "style": {"fontSize": "18px", "color": INK_SOFT}},
    },
    "legend": {
        "enabled": True,
        "align": "right",
        "layout": "vertical",
        "verticalAlign": "middle",
        "symbolHeight": 400,
        "itemStyle": {"color": INK_SOFT, "fontSize": "16px"},
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
    },
    "series": [
        {
            "type": "heatmap",
            "name": "Collaboration",
            "borderWidth": 0.5,
            "borderColor": PAGE_BG,
            "data": heatmap_data,
            "dataLabels": {"enabled": False},
        }
    ],
    "tooltip": {"enabled": True},
    "credits": {"enabled": False},
}

# Download Highcharts JS modules inline (required for headless Chrome)
_HC_URLS = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
_HM_URLS = [
    "https://code.highcharts.com/modules/heatmap.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/modules/heatmap.js",
]


def fetch_js(urls):
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except Exception:
            continue
    raise RuntimeError(f"Failed to download JS from: {urls}")


highcharts_js = fetch_js(_HC_URLS)
heatmap_js = fetch_js(_HM_URLS)

options_json = json.dumps(options)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:3600px; height:3600px;"></div>
    <script>Highcharts.chart('container', {options_json});</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Render PNG via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
