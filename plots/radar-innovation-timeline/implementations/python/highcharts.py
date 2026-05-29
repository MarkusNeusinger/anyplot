"""anyplot.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: highcharts | Python 3.13
Quality: pending | Updated: 2026-05-29
"""

import json
import math
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — hybrid-v3 sort
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Ring fills — Imprint green tint, theme-adaptive opacity
if THEME == "light":
    ring_fills_list = ["rgba(0,158,115,0.10)", "rgba(0,158,115,0.06)", "rgba(0,158,115,0.03)", "rgba(0,158,115,0.015)"]
else:
    ring_fills_list = ["rgba(0,158,115,0.18)", "rgba(0,158,115,0.12)", "rgba(0,158,115,0.07)", "rgba(0,158,115,0.03)"]

# Grid/spoke stroke color
RING_STROKE = "rgba(26,26,23,0.18)" if THEME == "light" else "rgba(240,239,232,0.18)"

# Data - Technology innovation radar (ThoughtWorks-inspired)
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

# 270° layout
num_sectors = len(sectors)
start_angle = 45.0
arc_span = 270.0
sector_span = arc_span / num_sectors

ring_radius_map = {"Adopt": 1.3, "Trial": 2.4, "Assess": 3.4, "Hold": 4.2}
marker_size_map = {"Adopt": 18, "Trial": 15, "Assess": 12, "Hold": 10}

# Imprint palette positions in canonical order for sectors
sector_colors = {
    "AI & ML": IMPRINT_PALETTE[0],  # #009E73 brand green
    "Cloud & DevOps": IMPRINT_PALETTE[1],  # #C475FD lavender
    "Security": IMPRINT_PALETTE[2],  # #4467A3 blue
    "Data Engineering": IMPRINT_PALETTE[3],  # #BD8233 ochre
}

# Ring label colors — semantic adoption progression
ring_label_colors = {
    "Adopt": "#009E73",  # green  = go
    "Trial": "#4467A3",  # blue   = explore
    "Assess": "#BD8233",  # ochre  = caution
    "Hold": "#AE3030",  # red    = stop
}

# Group items for angular spread within each (sector, ring) cell
items_by_group = {}
for item in innovations:
    key = (item["sector"], item["ring"])
    items_by_group.setdefault(key, []).append(item)

# Varied y-offset pool — more spread reduces label crowding vs. a single pair
ABOVE_OFFSETS = [-42, -54, -36, -60, -30, -48]
BELOW_OFFSETS = [36, 48, 30, 54, 42, 60]

# Compute polar positions and per-point label placement
for item in innovations:
    sector_idx = sectors.index(item["sector"])
    ring_r = ring_radius_map[item["ring"]]
    key = (item["sector"], item["ring"])
    group = items_by_group[key]
    pos = group.index(item)
    n = len(group)

    s_start = start_angle + sector_idx * sector_span + 4
    s_end = start_angle + (sector_idx + 1) * sector_span - 4
    step = (s_end - s_start) / max(n, 1)
    angle_deg = s_start + step * (pos + 0.5)

    jitter = np.random.uniform(-0.15, 0.15)
    radius = ring_r + jitter
    angle_rad = math.radians(angle_deg)
    item["x"] = round(radius * math.cos(angle_rad), 3)
    item["y"] = round(radius * math.sin(angle_rad), 3)
    item["angle_deg"] = angle_deg

    label_y = ABOVE_OFFSETS[pos % len(ABOVE_OFFSETS)] if pos % 2 == 0 else BELOW_OFFSETS[pos % len(BELOW_OFFSETS)]

    if 110 < angle_deg < 250:
        label_align, label_x = "right", -8
    elif angle_deg < 80 or angle_deg > 280:
        label_align, label_x = "left", 8
    else:
        label_align, label_x = "center", 0

    item["label_y"] = label_y
    item["label_x"] = label_x
    item["label_align"] = label_align

# Build per-sector scatter series
series_by_sector = {}
for item in innovations:
    series_by_sector.setdefault(item["sector"], []).append(item)

# Text outline for data labels: use page background so labels pop on both themes
text_outline = f"3px {PAGE_BG}"

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
                        "lineColor": PAGE_BG,
                    },
                    "dataLabels": {"y": d["label_y"], "x": d["label_x"], "align": d["label_align"]},
                }
                for d in items
            ],
            "marker": {"radius": 14, "symbol": "circle", "lineWidth": 3, "lineColor": PAGE_BG},
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "style": {"fontSize": "22px", "fontWeight": "normal", "color": INK, "textOutline": text_outline},
                "padding": 5,
            },
        }
    )

# Title — 60 chars, under 67 baseline, no scaling needed
title = "radar-innovation-timeline · python · highcharts · anyplot.ai"

highcharts_config = {
    "chart": {
        "type": "scatter",
        "width": 2400,
        "height": 2400,
        "backgroundColor": PAGE_BG,
        "spacing": [80, 80, 80, 80],
        "style": {"fontFamily": "'Segoe UI', Arial, sans-serif", "color": INK},
    },
    "title": {"text": title, "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK}, "margin": 20},
    "subtitle": {
        "text": "Technology Innovation Radar — Items mapped by adoption stage and domain",
        "style": {"fontSize": "28px", "color": INK_SOFT},
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
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "borderRadius": 12,
        "padding": 22,
        "itemStyle": {"fontSize": "28px", "fontWeight": "normal", "color": INK_SOFT},
        "itemMarginBottom": 10,
        "symbolRadius": 8,
        "symbolWidth": 24,
        "symbolHeight": 24,
        "title": {"text": "Sectors", "style": {"fontSize": "30px", "fontWeight": "bold", "color": INK}},
    },
    "tooltip": {
        "useHTML": True,
        "headerFormat": "",
        "pointFormat": (
            '<div style="font-size:22px"><b style="color:{series.color}">'
            "{point.name}</b><br/>Sector: {series.name}<br/>"
            "Stage: {point.custom.ring}</div>"
        ),
        "backgroundColor": ELEVATED_BG,
        "borderRadius": 8,
        "borderColor": INK_SOFT,
    },
    "plotOptions": {"scatter": {"marker": {"radius": 14}, "states": {"hover": {"marker": {"radius": 18}}}}},
    "credits": {"enabled": False},
    "series": chart_series,
}

config_json = json.dumps(highcharts_config)

# Renderer overlay: ring backgrounds, sector dividers, ring labels (single position)
sector_boundaries = [start_angle + i * sector_span for i in range(num_sectors + 1)]
sector_mid_angles = [(sector_boundaries[i] + sector_boundaries[i + 1]) / 2 for i in range(num_sectors)]

ring_data_js = json.dumps(
    {
        "radii": [1.3, 2.4, 3.4, 4.2],
        "fills": ring_fills_list,
        "names": ["Adopt", "Trial", "Assess", "Hold"],
        "colors": [ring_label_colors[r] for r in rings],
        "stroke": RING_STROKE,
    }
)

sector_data_js = json.dumps(
    {
        "names": sectors,
        "colors": [sector_colors[s] for s in sectors],
        "bounds": sector_boundaries,
        "mids": sector_mid_angles,
        "stroke": RING_STROKE,
    }
)

# Single ring label position at 48° — removes the duplicate-label clutter
renderer_js = f"""load: function() {{
    var c = this, cx = c.plotLeft + c.plotWidth / 2,
        cy = c.plotTop + c.plotHeight / 2,
        sx = c.plotWidth  / (c.xAxis[0].max - c.xAxis[0].min),
        sy = c.plotHeight / (c.yAxis[0].max - c.yAxis[0].min),
        sc = Math.min(sx, sy), R = {ring_data_js}, S = {sector_data_js}, i, a;
    for (i = R.radii.length - 1; i >= 0; i--)
        c.renderer.circle(cx, cy, R.radii[i] * sc).attr({{
            fill: R.fills[i], stroke: R.stroke,
            'stroke-width': 2, 'stroke-dasharray': '10,6', zIndex: 0}}).add();
    for (i = 0; i < S.bounds.length; i++) {{
        a = S.bounds[i] * Math.PI / 180;
        c.renderer.path(['M', cx, cy, 'L',
            cx + 4.2 * Math.cos(a) * sx, cy - 4.2 * Math.sin(a) * sy
        ]).attr({{stroke: S.stroke, 'stroke-width': 2, zIndex: 0}}).add();
    }}
    a = 48 * Math.PI / 180;
    for (i = 0; i < R.radii.length; i++)
        c.renderer.text(R.names[i],
            cx + R.radii[i] * Math.cos(a) * sx + 10,
            cy - R.radii[i] * Math.sin(a) * sy + 6
        ).attr({{zIndex: 5}}).css({{
            fontSize: '28px', fontWeight: 'bold', fontStyle: 'italic',
            color: R.colors[i], opacity: 0.9}}).add();
    for (i = 0; i < S.names.length; i++) {{
        a = S.mids[i] * Math.PI / 180;
        c.renderer.text(S.names[i],
            cx + 4.65 * Math.cos(a) * sx, cy - 4.65 * Math.sin(a) * sy
        ).attr({{zIndex: 3, align: 'center'}}).css({{
            fontSize: '32px', fontWeight: 'bold', color: S.colors[i]}}).add();
    }}
}}"""

# Download Highcharts JS for inline embedding (CDN blocked from file:// in headless)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 2400px; height: 2400px;"></div>
    <script>
    var config = {config_json};
    config.chart.events = {{{renderer_js}}};
    Highcharts.chart('container', config);
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML for Selenium screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=2400,2400")

driver = webdriver.Chrome(options=chrome_options)
# CDP override makes the viewport authoritative (--window-size alone loses ~139px to Chrome chrome)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 2400, "height": 2400, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# PIL normalization — pin to exact 2400×2400 so the post-render gate passes
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (2400, 2400):
    _norm = Image.new("RGB", (2400, 2400), PAGE_BG)
    _norm.paste(_img, ((2400 - _img.size[0]) // 2, (2400 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
