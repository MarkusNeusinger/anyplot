"""anyplot.ai
upset-basic: UpSet Plot for Multi-Set Intersection Analysis
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-05-13
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"
DOT_INACTIVE = "#D0CFC8" if THEME == "light" else "#3A3A35"

# Data — gene sets from 5 RNA-seq differential expression experiments
np.random.seed(42)
set_names = ["Hypoxia", "Heat Stress", "Nutrient Dep.", "UV Damage", "Oxidative"]
n_sets = len(set_names)
n_genes = 900
membership = np.column_stack([np.random.rand(n_genes) < p for p in [0.32, 0.28, 0.25, 0.22, 0.19]])
membership = membership[membership.any(axis=1)]
n_valid = len(membership)

set_sizes = membership.sum(axis=0).astype(int).tolist()

# Compute exclusive intersections (elements belonging to exactly these sets)
intersections = []
for combo_bits in range(1, 2**n_sets):
    mask = [(combo_bits >> i) & 1 for i in range(n_sets)]
    in_combo = np.ones(n_valid, dtype=bool)
    for i, m in enumerate(mask):
        if m:
            in_combo &= membership[:, i]
        else:
            in_combo &= ~membership[:, i]
    count = int(in_combo.sum())
    if count > 0:
        intersections.append({"mask": mask, "count": count})

intersections.sort(key=lambda x: -x["count"])
intersections = intersections[:15]
n_inter = len(intersections)

# Build dot matrix data
active_dots = []
inactive_dots = []
connector_series = []

for col, inter in enumerate(intersections):
    active_rows = [i for i, m in enumerate(inter["mask"]) if m]
    inactive_rows = [i for i, m in enumerate(inter["mask"]) if not m]
    for row in active_rows:
        active_dots.append([col, row])
    for row in inactive_rows:
        inactive_dots.append([col, row])
    if len(active_rows) > 1:
        connector_series.append(
            {
                "type": "line",
                "enableMouseTracking": False,
                "data": [[col, min(active_rows)], [col, max(active_rows)]],
                "color": BRAND,
                "lineWidth": 10,
                "marker": {"enabled": False},
                "showInLegend": False,
            }
        )

# Download Highcharts JS
hc_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.3.0/highcharts.js"
with urllib.request.urlopen(hc_url, timeout=30) as resp:
    highcharts_js = resp.read().decode("utf-8")

# Canvas layout
TOTAL_W, TOTAL_H = 4800, 2700
LEFT_W = 900
RIGHT_W = TOTAL_W - LEFT_W  # 3900
TOP_H = 1480
BOTTOM_H = TOTAL_H - TOP_H  # 1220

# Shared horizontal margins (so columns in bar chart align with dot matrix rows)
DOT_MARGIN_TOP = 20
DOT_MARGIN_BOTTOM = 100

# Chart 1: Intersection size bars (top right)
inter_config = {
    "chart": {
        "type": "column",
        "width": RIGHT_W,
        "height": TOP_H,
        "backgroundColor": PAGE_BG,
        "marginTop": 130,
        "marginRight": 60,
        "marginBottom": 40,
        "marginLeft": 140,
    },
    "title": {
        "text": "upset-basic · highcharts · anyplot.ai",
        "style": {"fontSize": "34px", "color": INK, "fontWeight": "600"},
    },
    "xAxis": {
        "min": -0.5,
        "max": n_inter - 0.5,
        "labels": {"enabled": False},
        "lineColor": INK_SOFT,
        "tickLength": 0,
        "gridLineWidth": 0,
    },
    "yAxis": {
        "title": {"text": "Intersection Size", "style": {"fontSize": "24px", "color": INK}},
        "labels": {"style": {"fontSize": "20px", "color": INK_SOFT}},
        "gridLineColor": GRID,
        "lineColor": INK_SOFT,
    },
    "series": [
        {
            "name": "Intersection Size",
            "data": [x["count"] for x in intersections],
            "color": BRAND,
            "borderWidth": 0,
            "pointPadding": 0.08,
            "groupPadding": 0.04,
            "showInLegend": False,
        }
    ],
    "legend": {"enabled": False},
    "credits": {"enabled": False},
    "tooltip": {"enabled": False},
}

# Chart 2: Set sizes (left panel, horizontal bars growing leftward)
set_config = {
    "chart": {
        "type": "bar",
        "width": LEFT_W,
        "height": BOTTOM_H,
        "backgroundColor": PAGE_BG,
        "marginTop": DOT_MARGIN_TOP,
        "marginRight": 10,
        "marginBottom": DOT_MARGIN_BOTTOM,
        "marginLeft": 160,
    },
    "title": {"text": ""},
    "xAxis": {
        "categories": set_names,
        "reversed": True,
        "labels": {"style": {"fontSize": "22px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickLength": 0,
        "gridLineWidth": 0,
    },
    "yAxis": {
        "title": {"text": "Set Size", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "gridLineColor": GRID,
        "reversed": True,
        "lineColor": INK_SOFT,
    },
    "series": [{"name": "Set Size", "data": set_sizes, "color": INK_SOFT, "borderWidth": 0, "showInLegend": False}],
    "legend": {"enabled": False},
    "credits": {"enabled": False},
    "tooltip": {"enabled": False},
}

# Chart 3: Dot matrix (bottom right)
dot_series = [
    {
        "type": "scatter",
        "enableMouseTracking": False,
        "name": "inactive",
        "data": inactive_dots,
        "marker": {"symbol": "circle", "radius": 20, "fillColor": DOT_INACTIVE, "lineWidth": 0},
        "showInLegend": False,
    },
    {
        "type": "scatter",
        "enableMouseTracking": False,
        "name": "active",
        "data": active_dots,
        "marker": {"symbol": "circle", "radius": 20, "fillColor": BRAND, "lineWidth": 0},
        "showInLegend": False,
    },
] + connector_series

dot_config = {
    "chart": {
        "width": RIGHT_W,
        "height": BOTTOM_H,
        "backgroundColor": PAGE_BG,
        "marginTop": DOT_MARGIN_TOP,
        "marginRight": 60,
        "marginBottom": DOT_MARGIN_BOTTOM,
        "marginLeft": 140,
    },
    "title": {"text": ""},
    "xAxis": {
        "min": -0.5,
        "max": n_inter - 0.5,
        "labels": {"enabled": False},
        "lineColor": "transparent",
        "tickLength": 0,
        "gridLineWidth": 0,
    },
    "yAxis": {
        "min": -0.5,
        "max": n_sets - 0.5,
        "reversed": True,
        "title": {"text": ""},
        "labels": {"enabled": False},
        "gridLineColor": GRID,
        "gridLineWidth": 1,
        "lineColor": "transparent",
        "tickLength": 0,
    },
    "series": dot_series,
    "legend": {"enabled": False},
    "credits": {"enabled": False},
    "tooltip": {"enabled": False},
}

# Build HTML with 3 positioned Highcharts instances
inter_json = json.dumps(inter_config)
set_json = json.dumps(set_config)
dot_json = json.dumps(dot_config)

separator_color = INK_SOFT

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG}; overflow:hidden;">
    <div style="position:relative; width:{TOTAL_W}px; height:{TOTAL_H}px; background:{PAGE_BG};">
        <div id="container-inter" style="position:absolute; left:{LEFT_W}px; top:0; width:{RIGHT_W}px; height:{TOP_H}px;"></div>
        <div id="container-sets" style="position:absolute; left:0; top:{TOP_H}px; width:{LEFT_W}px; height:{BOTTOM_H}px;"></div>
        <div id="container-dots" style="position:absolute; left:{LEFT_W}px; top:{TOP_H}px; width:{RIGHT_W}px; height:{BOTTOM_H}px;"></div>
        <div style="position:absolute; left:0; top:{TOP_H}px; width:{TOTAL_W}px; height:2px; background:{separator_color}; opacity:0.25;"></div>
    </div>
    <script>
        Highcharts.chart('container-inter', {inter_json});
        Highcharts.chart('container-sets', {set_json});
        Highcharts.chart('container-dots', {dot_json});
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument(f"--window-size={TOTAL_W},{TOTAL_H}")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
