""" anyplot.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: highcharts unknown | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-21
"""

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

CANVAS_W = 3200
CANVAS_H = 1800

# Data
np.random.seed(42)

metrics = [
    {
        "name": "CPU Usage",
        "value": 45,
        "unit": "%",
        "history": (30 + np.cumsum(np.random.randn(20) * 3)).clip(20, 80).tolist(),
        "change": -5.2,
        "status": "good",
    },
    {
        "name": "Memory",
        "value": 72,
        "unit": "%",
        "history": (60 + np.cumsum(np.random.randn(20) * 2)).clip(40, 90).tolist(),
        "change": 8.3,
        "status": "warning",
    },
    {
        "name": "Response Time",
        "value": 120,
        "unit": "ms",
        "history": (150 + np.cumsum(np.random.randn(20) * 10)).clip(80, 250).tolist(),
        "change": -15.0,
        "status": "good",
    },
    {
        "name": "Requests/sec",
        "value": 1250,
        "unit": "",
        "history": (1000 + np.cumsum(np.random.randn(20) * 50)).clip(800, 1500).tolist(),
        "change": 12.5,
        "status": "good",
    },
    {
        "name": "Error Rate",
        "value": 8.7,
        "unit": "%",
        "history": (2.0 + np.cumsum(np.random.randn(20) * 0.5)).clip(0.5, 10).tolist(),
        "change": 4.2,
        "status": "critical",
    },
    {
        "name": "Disk I/O",
        "value": 156,
        "unit": "MB/s",
        "history": (120 + np.cumsum(np.random.randn(20) * 15)).clip(80, 250).tolist(),
        "change": -3.2,
        "status": "good",
    },
]

status_colors = {"good": "#059669", "warning": "#D97706", "critical": "#DC2626"}
lower_is_better = {"CPU Usage", "Memory", "Response Time", "Error Rate"}

# Okabe-Ito position 1 for sparklines
SPARK_COLOR = "#009E73"

# Layout constants
COLS = 3
ROWS = 2
PADDING_H = 60
PADDING_V = 50
GAP_X = 50
GAP_Y = 40
TITLE_H = 130

TILE_W = (CANVAS_W - 2 * PADDING_H - (COLS - 1) * GAP_X) // COLS
TILE_H = (CANVAS_H - TITLE_H - 2 * PADDING_V - (ROWS - 1) * GAP_Y) // ROWS

# Download Highcharts JS
highcharts_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/12.2.0/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Build tiles HTML and JS
tiles_html = ""
tiles_js = ""

for i, m in enumerate(metrics):
    row = i // COLS
    col = i % COLS
    left = PADDING_H + col * (TILE_W + GAP_X)
    top = TITLE_H + PADDING_V + row * (TILE_H + GAP_Y)

    status_color = status_colors[m["status"]]
    favorable = (m["change"] <= 0) if m["name"] in lower_is_better else (m["change"] >= 0)
    change_color = "#059669" if favorable else "#DC2626"
    arrow = "▲" if m["change"] >= 0 else "▼"
    change_text = f"{arrow} {abs(m['change']):.1f}%"

    if m["value"] >= 1000:
        value_str = f"{m['value']:,.0f}"
    elif isinstance(m["value"], float):
        value_str = f"{m['value']:.1f}"
    else:
        value_str = str(m["value"])

    chart_id = f"chart_{i}"
    sparkline_data = m["history"]

    tiles_html += f"""
    <div style="
        position: absolute;
        left: {left}px;
        top: {top}px;
        width: {TILE_W}px;
        height: {TILE_H}px;
        background: {ELEVATED_BG};
        border-radius: 16px;
        border-left: 10px solid {status_color};
        padding: 40px 40px 28px 40px;
        box-sizing: border-box;
    ">
        <div style="font-size: 34px; color: {INK_SOFT}; font-weight: 500; margin-bottom: 14px; letter-spacing: 0.5px;">
            {m["name"]}
        </div>
        <div style="display: flex; align-items: baseline; margin-bottom: 18px;">
            <span style="font-size: 88px; font-weight: 700; color: {INK}; line-height: 1;">
                {value_str}
            </span>
            <span style="font-size: 40px; color: {INK_SOFT}; margin-left: 12px;">
                {m["unit"]}
            </span>
        </div>
        <div style="font-size: 30px; color: {change_color}; font-weight: 600; margin-bottom: 24px;">
            {change_text}
        </div>
        <div id="{chart_id}" style="width: 100%; height: 300px;"></div>
    </div>
    """

    tiles_js += f"""
    Highcharts.chart('{chart_id}', {{
        chart: {{
            type: 'area',
            backgroundColor: 'transparent',
            margin: [4, 0, 4, 0],
            spacing: [0, 0, 0, 0],
            animation: false
        }},
        title: {{ text: null }},
        credits: {{ enabled: false }},
        xAxis: {{ visible: false }},
        yAxis: {{ visible: false }},
        legend: {{ enabled: false }},
        tooltip: {{ enabled: false }},
        plotOptions: {{
            area: {{
                fillColor: {{
                    linearGradient: {{ x1: 0, y1: 0, x2: 0, y2: 1 }},
                    stops: [
                        [0, '{SPARK_COLOR}55'],
                        [1, '{SPARK_COLOR}08']
                    ]
                }},
                lineWidth: 7,
                color: '{SPARK_COLOR}',
                marker: {{ enabled: false }},
                states: {{ hover: {{ enabled: false }} }}
            }}
        }},
        series: [{{ data: {sparkline_data} }}]
    }});
    """

# Full dashboard HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        * {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    </style>
</head>
<body style="margin: 0; padding: 0; background: {PAGE_BG}; width: {CANVAS_W}px; height: {CANVAS_H}px; overflow: hidden;">
    <div style="position: relative; width: {CANVAS_W}px; height: {CANVAS_H}px;">
        <div style="
            position: absolute; left: 0; top: 0;
            width: {CANVAS_W}px; height: {TITLE_H}px;
            display: flex; align-items: center; justify-content: center;
            font-size: 52px; font-weight: 700; color: {INK};
        ">
            dashboard-metrics-tiles · python · highcharts · anyplot.ai
        </div>
        {tiles_html}
    </div>
    <script>{tiles_js}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument(f"--window-size={CANVAS_W},{CANVAS_H}")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride",
    {"width": CANVAS_W, "height": CANVAS_H, "deviceScaleFactor": 1, "mobile": False},
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# PIL safety net: pin to exact dimensions
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (CANVAS_W, CANVAS_H):
    _norm = Image.new("RGB", (CANVAS_W, CANVAS_H), PAGE_BG)
    _norm.paste(_img, ((CANVAS_W - _img.size[0]) // 2, (CANVAS_H - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
