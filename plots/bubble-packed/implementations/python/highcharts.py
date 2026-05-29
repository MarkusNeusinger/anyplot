""" anyplot.ai
bubble-packed: Basic Packed Bubble Chart
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-29
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

# Imprint categorical palette — canonical order, hybrid-v3 sort
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Canvas: square format for symmetric packed bubble layout
W, H = 2400, 2400

# Data — market value by sector ($B), 5 sectors, 20 items
sectors = [
    {
        "name": "Technology",
        "items": [("Software", 850), ("Cloud", 680), ("Hardware", 420), ("Semicon.", 390), ("Cybersec.", 280)],
    },
    {"name": "Finance", "items": [("Banking", 720), ("Insurance", 480), ("Asset Mgmt", 350), ("Fintech", 260)]},
    {"name": "Healthcare", "items": [("Pharma", 580), ("Biotech", 420), ("Med Devices", 320), ("Health Svcs", 240)]},
    {"name": "Energy", "items": [("Oil & Gas", 550), ("Renewables", 380), ("Utilities", 290)]},
    {"name": "Consumer", "items": [("Automotive", 510), ("Retail", 460), ("Food & Bev", 340), ("Entertain.", 270)]},
]

# Chart setup
chart = Chart(container="container")
chart.options = HighchartsOptions()

title = "Global Market Capitalization · bubble-packed · python · highcharts · anyplot.ai"
title_len = len(title)
title_fs = round(66 * min(1.0, 67 / title_len))
title_fs = max(title_fs, 44)

chart.options.chart = {
    "type": "packedbubble",
    "width": W,
    "height": H,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK, "fontFamily": "system-ui, sans-serif"},
    "margin": [60, 20, 110, 20],
}

chart.options.title = {
    "text": title,
    "style": {"fontSize": f"{title_fs}px", "fontWeight": "600", "color": INK},
    "margin": 8,
}

chart.options.subtitle = {
    "text": "Market value by sector ($B)",
    "style": {"fontSize": "44px", "color": INK_SOFT, "fontWeight": "400"},
    "margin": 16,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "useHTML": True,
    "style": {"fontSize": "32px"},
    "pointFormat": "<b>{point.name}</b>: ${point.value}B",
}

chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "itemStyle": {"color": INK_SOFT, "fontSize": "44px", "fontWeight": "500"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolHeight": 16,
    "symbolWidth": 24,
    "symbolRadius": 8,
    "padding": 14,
    "margin": 18,
    "itemDistance": 30,
}

# Explicitly hide axes to prevent rendering artifacts in packedbubble
chart.options.x_axis = {"visible": False}
chart.options.y_axis = {"visible": False, "gridLineWidth": 0}

chart.options.plot_options = {
    "packedbubble": {
        "minSize": 140,
        "maxSize": 560,
        "zMin": 0,
        "zMax": 1000,
        "layoutAlgorithm": {
            "gravitationalConstant": 0.12,
            "splitSeries": True,
            "seriesInteraction": True,
            "dragBetweenSeries": False,
            "parentNodeLimit": True,
            "parentNodeOptions": {
                "gravitationalConstant": 0.15,
                "marker": {"fillOpacity": 0.08, "lineWidth": 2, "lineColor": "rgba(0,0,0,0.25)"},
            },
            "bubblePadding": 4,
        },
        "dataLabels": {
            "enabled": True,
            "format": "{point.name}",
            "filter": {"property": "y", "operator": ">", "value": 200},
            "style": {"fontSize": "28px", "fontWeight": "600", "color": "white", "textOutline": "2px rgba(0,0,0,0.5)"},
        },
        "marker": {"lineWidth": 2, "lineColor": "rgba(255,255,255,0.4)"},
    }
}

# Series with Imprint palette and per-bubble opacity hierarchy
series_list = []
for i, sector in enumerate(sectors):
    enriched_data = [
        {"name": name, "value": val, "marker": {"fillOpacity": 0.65 + 0.35 * (val / 850)}}
        for name, val in sector["items"]
    ]
    series_list.append(
        {"type": "packedbubble", "name": sector["name"], "data": enriched_data, "color": IMPRINT_PALETTE[i]}
    )

chart.options.series = series_list

# Download Highcharts JS inline — CDN blocked in headless file:// context
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts-more.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:{W}px; height:{H}px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome with authoritative CDP viewport override
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument(f"--window-size={W},{H}")

driver = webdriver.Chrome(options=chrome_options)
# CDP override is authoritative — --window-size alone loses ~139px to Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Safety net: pad/crop to exact target dimensions if CDP rounding drifts
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (W, H):
    _norm = Image.new("RGB", (W, H), PAGE_BG)
    _norm.paste(_img, ((W - _img.size[0]) // 2, (H - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
