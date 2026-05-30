"""anyplot.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-30
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
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

# Imprint palette — semantic mapping for 5-level Likert opinion scale
# Positive→neutral→negative maps to green→muted→red per Imprint semantic anchors
CATEGORY_COLORS = {
    "Strongly Agree": "#009E73",  # Imprint brand green — positive
    "Agree": "#99B314",  # Imprint lime — growth / positive leaning
    "Neutral": INK_MUTED,  # Imprint muted anchor — neither positive nor negative
    "Disagree": "#BD8233",  # Imprint ochre — cautionary
    "Strongly Disagree": "#AE3030",  # Imprint matte red — negative / bad
}

# Data — employee satisfaction survey, ~895 employees, 4 quarterly waves
# Topic: "Should the company expand its professional development program?"
waves = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]

flows = [
    # Q1 → Q2: after initial program improvements announced
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
    # Q2 → Q3: after new mentorship programme launches
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
    # Q3 → Q4: after satisfaction results shared company-wide
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

# Calculate node totals for respondent-count labels
node_outgoing = {}
node_incoming = {}
for source, target, count in flows:
    node_outgoing[source] = node_outgoing.get(source, 0) + count
    node_incoming[target] = node_incoming.get(target, 0) + count

nodes_data = []
for wave_idx in range(len(waves)):
    for cat in categories:
        node_id = f"{cat}_{wave_idx}"
        total = node_outgoing.get(node_id, 0) if wave_idx == 0 else node_incoming.get(node_id, 0)
        nodes_data.append(
            {"id": node_id, "name": f"{cat} ({total})", "column": wave_idx, "color": CATEGORY_COLORS[cat]}
        )

# Per-link RGBA: stable flows are opaque, opinion-change flows are faint
links_data = []
for source, target, weight in flows:
    source_cat = source.rsplit("_", 1)[0]
    target_cat = target.rsplit("_", 1)[0]
    is_stable = source_cat == target_cat
    hex_col = CATEGORY_COLORS[source_cat]
    r, g, b = int(hex_col[1:3], 16), int(hex_col[3:5], 16), int(hex_col[5:7], 16)
    alpha = 0.7 if is_stable else 0.28
    links_data.append({"from": source, "to": target, "weight": weight, "color": f"rgba({r},{g},{b},{alpha})"})

# Title with length-scaled fontsize (baseline 66px for ~67-char title)
title_text = "Employee Training Satisfaction · alluvial-opinion-flow · python · highcharts · anyplot.ai"
title_fontsize = max(44, round(66 * 67 / len(title_text)))

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "sankey",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginLeft": 180,
    "marginRight": 440,
    "marginTop": 285,
    "marginBottom": 145,
}

chart.options.title = {
    "text": title_text,
    "style": {"fontSize": f"{title_fontsize}px", "fontWeight": "bold", "color": INK, "fontFamily": "Georgia, serif"},
}

chart.options.subtitle = {
    "text": '"Should the company expand its professional development program?" — 895 employees tracked quarterly',
    "style": {"fontSize": "28px", "color": INK_SOFT, "fontFamily": "Georgia, serif"},
}

chart.options.tooltip = {
    "style": {"fontSize": "24px"},
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
            "fontSize": "26px",
            "fontWeight": "bold",
            "color": INK,
            "textOutline": f"4px {PAGE_BG}",
            "fontFamily": "Arial, sans-serif",
        },
        "nodeFormat": "{point.name}",
    },
    "nodeWidth": 40,
    "nodePadding": 32,
    "linkOpacity": 1,
    "curveFactor": 0.5,
}

chart.options.series = [series_config]

# Wave column header annotations — positioned in the dedicated top margin area
# marginTop=285 gives ~285px above the chart plot area for column headers (y≈165)
# Inner width: 3200 - 180 - 440 = 2580; columns spaced at ~0, ~860, ~1720, ~2580
wave_x_positions = [220, 1050, 1880, 2690]

# Narrative focal point: Positive sentiment (Strongly Agree + Agree) grew Q1→Q4
# Q1 positive: 430/895 ≈ 48%  →  Q4 positive: 475/900 ≈ 53%
narrative_text = "Positive sentiment (Agree+Strongly Agree)<br/>grew from <b>48% → 53%</b> Q1→Q4"

chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": wave_x_positions[i], "y": 165},
                "text": wave,
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "style": {"fontSize": "34px", "fontWeight": "bold", "color": INK, "fontFamily": "Georgia, serif"},
            }
            for i, wave in enumerate(waves)
        ],
        "labelOptions": {"useHTML": True},
    },
    {
        "labels": [
            {
                "point": {"x": 2850, "y": 800},
                "text": narrative_text,
                "backgroundColor": ELEVATED_BG,
                "borderColor": "#009E73",
                "borderWidth": 3,
                "borderRadius": 8,
                "padding": 14,
                "style": {"fontSize": "26px", "color": INK, "fontFamily": "Georgia, serif", "textOutline": "none"},
            }
        ],
        "labelOptions": {"useHTML": True, "crop": False},
    },
]

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

# Load JS modules — local cache first, CDN fallback
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

html_str = chart.to_js_literal()

# Custom HTML legend for category colors and flow-opacity key
legend_html = f"""
<div id="custom-legend" style="position: absolute; bottom: 28px; left: 50%;
     transform: translateX(-50%); display: flex; gap: 36px;
     font-family: Georgia, serif; font-size: 22px; color: {INK};
     align-items: center; flex-wrap: wrap; justify-content: center;
     background: {ELEVATED_BG}; padding: 10px 28px; border-radius: 6px;">
  <div style="display:flex;align-items:center;gap:9px;">
    <div style="width:26px;height:16px;background:#009E73;border-radius:3px;"></div>
    <span>Strongly Agree</span>
  </div>
  <div style="display:flex;align-items:center;gap:9px;">
    <div style="width:26px;height:16px;background:#99B314;border-radius:3px;"></div>
    <span>Agree</span>
  </div>
  <div style="display:flex;align-items:center;gap:9px;">
    <div style="width:26px;height:16px;background:{INK_MUTED};border-radius:3px;"></div>
    <span>Neutral</span>
  </div>
  <div style="display:flex;align-items:center;gap:9px;">
    <div style="width:26px;height:16px;background:#BD8233;border-radius:3px;"></div>
    <span>Disagree</span>
  </div>
  <div style="display:flex;align-items:center;gap:9px;">
    <div style="width:26px;height:16px;background:#AE3030;border-radius:3px;"></div>
    <span>Strongly Disagree</span>
  </div>
  <span style="margin-left:18px;border-left:2px solid {INK_SOFT};padding-left:18px;color:{INK_SOFT};">
    Opaque flow = stable opinion &nbsp;|&nbsp; Faint = opinion changed
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
<body style="margin:0; position:relative; background-color:{PAGE_BG};">
    <div id="container" style="width:3200px; height:1800px;"></div>
    {legend_html}
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact (theme-suffixed, uses CDN for standalone viewing)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with authoritative CDP viewport override
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin PNG to exact 3200×1800 (guards against ±1–2 px CDP rounding)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
