""" pyplots.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: highcharts unknown | Python 3.14.3
Quality: 90/100 | Created: 2026-02-18
"""

import json
import math
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Technology innovation radar inspired by ThoughtWorks Technology Radar
np.random.seed(42)

sectors = ["AI & ML", "Cloud & DevOps", "Security", "Data Engineering"]
rings = ["Adopt", "Trial", "Assess", "Hold"]

innovations = [
    {"name": "LLM Code Review", "sector": "AI & ML", "ring": "Adopt"},
    {"name": "ML Feature Stores", "sector": "AI & ML", "ring": "Adopt"},
    {"name": "AI Pair Programming", "sector": "AI & ML", "ring": "Trial"},
    {"name": "Retrieval-Augmented Gen.", "sector": "AI & ML", "ring": "Trial"},
    {"name": "AI Automated Testing", "sector": "AI & ML", "ring": "Trial"},
    {"name": "Multimodal Models", "sector": "AI & ML", "ring": "Assess"},
    {"name": "Autonomous AI Agents", "sector": "AI & ML", "ring": "Assess"},
    {"name": "Neuromorphic Computing", "sector": "AI & ML", "ring": "Hold"},
    {"name": "Platform Engineering", "sector": "Cloud & DevOps", "ring": "Adopt"},
    {"name": "GitOps Workflows", "sector": "Cloud & DevOps", "ring": "Adopt"},
    {"name": "FinOps Practices", "sector": "Cloud & DevOps", "ring": "Trial"},
    {"name": "WebAssembly Runtimes", "sector": "Cloud & DevOps", "ring": "Trial"},
    {"name": "Developer Portals", "sector": "Cloud & DevOps", "ring": "Assess"},
    {"name": "Edge-Native Apps", "sector": "Cloud & DevOps", "ring": "Assess"},
    {"name": "Serverless Containers", "sector": "Cloud & DevOps", "ring": "Hold"},
    {"name": "Zero Trust Architecture", "sector": "Security", "ring": "Adopt"},
    {"name": "Supply Chain Security", "sector": "Security", "ring": "Adopt"},
    {"name": "SBOM Automation", "sector": "Security", "ring": "Trial"},
    {"name": "Confidential Computing", "sector": "Security", "ring": "Trial"},
    {"name": "Post-Quantum Crypto", "sector": "Security", "ring": "Assess"},
    {"name": "AI Threat Detection", "sector": "Security", "ring": "Assess"},
    {"name": "Homomorphic Encryption", "sector": "Security", "ring": "Hold"},
    {"name": "Data Mesh Architecture", "sector": "Data Engineering", "ring": "Adopt"},
    {"name": "Stream Processing", "sector": "Data Engineering", "ring": "Trial"},
    {"name": "Lakehouse Architecture", "sector": "Data Engineering", "ring": "Trial"},
    {"name": "Data Contracts", "sector": "Data Engineering", "ring": "Trial"},
    {"name": "Semantic Layer Platforms", "sector": "Data Engineering", "ring": "Assess"},
    {"name": "Vector Databases", "sector": "Data Engineering", "ring": "Assess"},
    {"name": "Quantum Data Processing", "sector": "Data Engineering", "ring": "Hold"},
]

# 270° layout: leaves the right side open for legend (spec recommendation)
num_sectors = len(sectors)
start_angle = 45.0
arc_span = 270.0
sector_span = arc_span / num_sectors

# Increased inner ring radius to reduce label crowding
ring_radius_map = {"Adopt": 1.3, "Trial": 2.4, "Assess": 3.4, "Hold": 4.2}
# Marker sizes vary by ring for visual hierarchy / data storytelling
marker_size_map = {"Adopt": 18, "Trial": 15, "Assess": 12, "Hold": 10}
# Label offsets scaled by ring (inner rings need more separation)
ring_offsets = {"Adopt": (-30, 34), "Trial": (-26, 30), "Assess": (-24, 28), "Hold": (-22, 26)}

sector_colors = {
    "AI & ML": "#306998",
    "Cloud & DevOps": "#D4762C",
    "Security": "#3C9150",
    "Data Engineering": "#8C50A0",
}

# Group items for positioning
items_by_group = {}
for item in innovations:
    key = (item["sector"], item["ring"])
    items_by_group.setdefault(key, []).append(item)

# Compute positions and per-point label placement
for item in innovations:
    sector_idx = sectors.index(item["sector"])
    ring_r = ring_radius_map[item["ring"]]
    key = (item["sector"], item["ring"])
    group = items_by_group[key]
    pos = group.index(item)
    n = len(group)

    s_start = start_angle + sector_idx * sector_span + 5
    s_end = start_angle + (sector_idx + 1) * sector_span - 5
    step = (s_end - s_start) / max(n, 1)
    angle_deg = s_start + step * (pos + 0.5)

    jitter = np.random.uniform(-0.18, 0.18)
    radius = ring_r + jitter
    angle_rad = math.radians(angle_deg)
    item["x"] = round(radius * math.cos(angle_rad), 3)
    item["y"] = round(radius * math.sin(angle_rad), 3)
    item["angle_deg"] = angle_deg

    above_y, below_y = ring_offsets[item["ring"]]
    label_y = above_y if pos % 2 == 0 else below_y

    if 110 < angle_deg < 250:
        label_align, label_x = "right", -8
    elif angle_deg < 80 or angle_deg > 280:
        label_align, label_x = "left", 8
    else:
        label_align, label_x = "center", 0

    item["label_y"] = label_y
    item["label_x"] = label_x
    item["label_align"] = label_align

# Build Highcharts series with per-point marker sizes and label offsets
series_by_sector = {}
for item in innovations:
    series_by_sector.setdefault(item["sector"], []).append(item)

chart_series = []
for sector in sectors:
    items = series_by_sector[sector]
    chart_series.append(
        {
            "type": "scatter",
            "name": sector,
            "color": sector_colors[sector],
            "data": [
                {
                    "x": d["x"],
                    "y": d["y"],
                    "name": d["name"],
                    "custom": {"ring": d["ring"]},
                    "marker": {
                        "radius": marker_size_map[d["ring"]],
                        "symbol": "circle",
                        "lineWidth": 3,
                        "lineColor": "#ffffff",
                    },
                    "dataLabels": {"y": d["label_y"], "x": d["label_x"], "align": d["label_align"]},
                }
                for d in items
            ],
            "marker": {"radius": 14, "symbol": "circle", "lineWidth": 3, "lineColor": "#ffffff"},
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "style": {"fontSize": "22px", "fontWeight": "normal", "color": "#333333", "textOutline": "3px white"},
                "padding": 5,
            },
        }
    )

# Chart configuration - square format for circular chart
highcharts_config = {
    "chart": {
        "type": "scatter",
        "width": 3600,
        "height": 3600,
        "backgroundColor": "#fafafa",
        "spacing": [80, 80, 80, 80],
        "style": {"fontFamily": "'Segoe UI', Arial, sans-serif"},
    },
    "title": {
        "text": "radar-innovation-timeline \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "bold", "color": "#2a2a2a"},
        "margin": 20,
    },
    "subtitle": {
        "text": "Technology Innovation Radar \u2014 Items mapped by adoption stage and domain",
        "style": {"fontSize": "30px", "color": "#666666"},
    },
    "xAxis": {
        "min": -5.2,
        "max": 5.2,
        "gridLineWidth": 0,
        "lineWidth": 0,
        "tickWidth": 0,
        "labels": {"enabled": False},
        "title": {"text": None},
    },
    "yAxis": {
        "min": -5.2,
        "max": 5.2,
        "gridLineWidth": 0,
        "lineWidth": 0,
        "tickWidth": 0,
        "labels": {"enabled": False},
        "title": {"text": None},
    },
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "middle",
        "layout": "vertical",
        "x": -40,
        "y": 20,
        "floating": True,
        "backgroundColor": "rgba(255, 255, 255, 0.94)",
        "borderColor": "#dddddd",
        "borderWidth": 1,
        "borderRadius": 12,
        "padding": 22,
        "itemStyle": {"fontSize": "28px", "fontWeight": "normal", "color": "#333333"},
        "itemMarginBottom": 10,
        "symbolRadius": 8,
        "symbolWidth": 24,
        "symbolHeight": 24,
        "title": {"text": "Sectors", "style": {"fontSize": "32px", "fontWeight": "bold", "color": "#333333"}},
    },
    "tooltip": {
        "useHTML": True,
        "headerFormat": "",
        "pointFormat": '<div style="font-size:22px"><b style="color:{series.color}">'
        "{point.name}</b><br/>Sector: {series.name}<br/>"
        "Stage: {point.custom.ring}</div>",
        "backgroundColor": "rgba(255, 255, 255, 0.96)",
        "borderRadius": 8,
        "borderColor": "#cccccc",
    },
    "plotOptions": {"scatter": {"marker": {"radius": 14}, "states": {"hover": {"marker": {"radius": 18}}}}},
    "credits": {"enabled": False},
    "series": chart_series,
}

config_json = json.dumps(highcharts_config)

# Renderer overlay data for ring backgrounds, sector lines, labels
sector_boundaries = [start_angle + i * sector_span for i in range(num_sectors + 1)]
sector_mid_angles = [(sector_boundaries[i] + sector_boundaries[i + 1]) / 2 for i in range(num_sectors)]

ring_data_js = json.dumps(
    {
        "radii": [1.3, 2.4, 3.4, 4.2],
        "fills": ["rgba(48,105,152,0.08)", "rgba(48,105,152,0.05)", "rgba(48,105,152,0.03)", "rgba(48,105,152,0.015)"],
        "names": ["Adopt", "Trial", "Assess", "Hold"],
        "colors": ["#2a7d3a", "#b8860b", "#cc6600", "#993333"],
    }
)

sector_data_js = json.dumps(
    {
        "names": sectors,
        "colors": [sector_colors[s] for s in sectors],
        "bounds": sector_boundaries,
        "mids": sector_mid_angles,
    }
)

# Renderer callback uses chart properties for pixel-accurate positioning
renderer_js = f"""load: function() {{
            var c = this, cx = c.plotLeft + c.plotWidth / 2,
                cy = c.plotTop + c.plotHeight / 2,
                sx = c.plotWidth / (c.xAxis[0].max - c.xAxis[0].min),
                sy = c.plotHeight / (c.yAxis[0].max - c.yAxis[0].min),
                sc = Math.min(sx, sy), R = {ring_data_js}, S = {sector_data_js}, i, a;
            for (i = R.radii.length - 1; i >= 0; i--)
                c.renderer.circle(cx, cy, R.radii[i] * sc).attr({{
                    fill: R.fills[i], stroke: 'rgba(0,0,0,0.12)',
                    'stroke-width': 2, 'stroke-dasharray': '10,6', zIndex: 0}}).add();
            for (i = 0; i < S.bounds.length; i++) {{
                a = S.bounds[i] * Math.PI / 180;
                c.renderer.path(['M', cx, cy, 'L',
                    cx + 4.2 * Math.cos(a) * sx, cy - 4.2 * Math.sin(a) * sy
                ]).attr({{stroke: 'rgba(0,0,0,0.12)', 'stroke-width': 2, zIndex: 0}}).add();
            }}
            a = 48 * Math.PI / 180;
            for (i = 0; i < R.radii.length; i++)
                c.renderer.text(R.names[i],
                    cx + R.radii[i] * Math.cos(a) * sx + 10,
                    cy - R.radii[i] * Math.sin(a) * sy + 6
                ).attr({{zIndex: 5}}).css({{
                    fontSize: '28px', fontWeight: 'bold', fontStyle: 'italic',
                    color: R.colors[i], opacity: 0.85}}).add();
            a = 313 * Math.PI / 180;
            for (i = 0; i < R.radii.length; i++)
                c.renderer.text(R.names[i],
                    cx + R.radii[i] * Math.cos(a) * sx - 10,
                    cy - R.radii[i] * Math.sin(a) * sy + 6
                ).attr({{zIndex: 5}}).css({{
                    fontSize: '24px', fontWeight: '600', fontStyle: 'italic',
                    color: R.colors[i], opacity: 0.7}}).add();
            for (i = 0; i < S.names.length; i++) {{
                a = S.mids[i] * Math.PI / 180;
                c.renderer.text(S.names[i],
                    cx + 4.65 * Math.cos(a) * sx, cy - 4.65 * Math.sin(a) * sy
                ).attr({{zIndex: 3, align: 'center'}}).css({{
                    fontSize: '32px', fontWeight: 'bold', color: S.colors[i]}}).add();
            }}
        }}"""

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Static HTML for screenshot
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background: #fafafa;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>
    var config = {config_json};
    config.chart.events = {{{renderer_js}}};
    Highcharts.chart('container', config);
    </script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Interactive HTML version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(
        f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
</head>
<body style="margin:0; background: #fafafa;">
    <div id="container" style="width: 100vmin; height: 100vmin; margin: 0 auto;"></div>
    <script>
    var config = {config_json};
    config.chart.width = null;
    config.chart.height = null;
    config.chart.events = {{{renderer_js}}};
    Highcharts.chart('container', config);
    </script>
</body>
</html>"""
    )

# Screenshot with Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
