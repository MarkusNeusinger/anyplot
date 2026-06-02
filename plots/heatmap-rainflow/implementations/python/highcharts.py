""" anyplot.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Updated: 2026-06-02
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
NULL_COLOR = "#E0DECE" if THEME == "light" else "#2A2A26"

# Canvas — 2400×2400 square (heatmap, symmetric axes)
CANVAS_W, CANVAS_H = 2400, 2400

# Data — simulated rainflow counting matrix from variable-amplitude loading
np.random.seed(42)
n_amp_bins = 20
n_mean_bins = 20

amplitude_bins = np.linspace(10, 200, n_amp_bins)
mean_bins = np.linspace(-50, 250, n_mean_bins)

amp_grid, mean_grid = np.meshgrid(amplitude_bins, mean_bins, indexing="ij")
amp_factor = np.exp(-0.025 * amp_grid)
mean_factor = np.exp(-0.5 * ((mean_grid - 100) / 38) ** 2)

raw_counts = amp_factor * mean_factor * 5000
raw_counts += np.random.exponential(scale=raw_counts * 0.15 + 1)
cycle_counts = np.round(raw_counts).astype(int)
cycle_counts = np.clip(cycle_counts, 0, None)
cycle_counts[cycle_counts < 3] = 0

amp_labels = [f"{v:.0f}" for v in amplitude_bins]
mean_labels = [f"{v:.0f}" for v in mean_bins]

heatmap_data = []
max_count = 0
for y_idx in range(n_amp_bins):
    for x_idx in range(n_mean_bins):
        val = int(cycle_counts[y_idx, x_idx])
        if val > max_count:
            max_count = val
        heatmap_data.append([x_idx, y_idx, val if val > 0 else None])

# Chart — Highcharts heatmap with Imprint sequential colormap (imprint_seq)
title = "heatmap-rainflow · python · highcharts · anyplot.ai"

chart = Chart(container="container")
chart.options = HighchartsOptions.from_dict(
    {
        "chart": {
            "type": "heatmap",
            "width": CANVAS_W,
            "height": CANVAS_H,
            "backgroundColor": PAGE_BG,
            "marginTop": 280,
            "plotBorderWidth": 0,
            "marginBottom": 230,
            "marginRight": 420,
            "marginLeft": 290,
            "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
        },
        "title": {"text": title, "style": {"fontSize": "66px", "fontWeight": "600", "color": INK}, "y": 50},
        "subtitle": {
            "text": "Rainflow cycle counting — dominant cycles at low amplitude, near 100 MPa mean stress",
            "style": {"fontSize": "48px", "fontWeight": "normal", "color": INK_SOFT},
            "y": 134,
        },
        "xAxis": {
            "categories": mean_labels,
            "title": {
                "text": "Cycle Mean (MPa)",
                "style": {"fontSize": "56px", "fontWeight": "600", "color": INK},
                "margin": 20,
            },
            "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "rotation": 315, "y": 30},
            "lineWidth": 0,
            "tickLength": 0,
        },
        "yAxis": {
            "categories": amp_labels,
            "title": {
                "text": "Cycle Amplitude (MPa)",
                "style": {"fontSize": "56px", "fontWeight": "600", "color": INK},
                "margin": 20,
            },
            "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
            "reversed": False,
            "lineWidth": 0,
            "gridLineWidth": 0,
        },
        "colorAxis": {
            "min": 1,
            "max": int(max_count),
            "type": "logarithmic",
            "stops": [[0, "#009E73"], [0.5, "#22828B"], [1, "#4467A3"]],
            "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
        },
        "legend": {
            "title": {"text": "Cycle Count", "style": {"fontSize": "44px", "fontWeight": "600", "color": INK}},
            "align": "right",
            "layout": "vertical",
            "verticalAlign": "middle",
            "symbolHeight": 720,
            "symbolWidth": 36,
            "itemStyle": {"fontSize": "44px", "color": INK_SOFT},
            "x": -30,
            "margin": 60,
        },
        "tooltip": {
            "style": {"fontSize": "30px"},
            "headerFormat": "",
            "pointFormat": (
                "Amplitude: <b>{series.yAxis.categories.(point.y)} MPa</b><br>"
                "Mean: <b>{series.xAxis.categories.(point.x)} MPa</b><br>"
                "Cycles: <b>{point.value}</b>"
            ),
        },
        "credits": {"enabled": False},
        "plotOptions": {"heatmap": {"colsize": 1, "rowsize": 1}},
        "series": [
            {
                "type": "heatmap",
                "name": "Cycle Count",
                "data": heatmap_data,
                "borderWidth": 2,
                "borderColor": PAGE_BG,
                "nullColor": NULL_COLOR,
            }
        ],
    }
)

js_literal = chart.to_js_literal()

# Download Highcharts core and heatmap module inline (CDN unavailable in headless file://)
urls = {
    "highcharts": "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js",
    "heatmap": "https://cdn.jsdelivr.net/npm/highcharts/modules/heatmap.js",
}
scripts = {}
for name, url in urls.items():
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                scripts[name] = response.read().decode("utf-8")
            break
        except Exception:
            time.sleep(2 * (attempt + 1))
    else:
        raise RuntimeError(f"Failed to download {url}")

highcharts_js = scripts["highcharts"]
heatmap_js = scripts["heatmap"]

# Theme-adaptive annotation styling
ann_fill = "rgba(255,253,246,0.93)" if THEME == "light" else "rgba(36,36,32,0.93)"
ann_text = INK
ann_stroke = INK_SOFT

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:{PAGE_BG};">
    <div id="container" style="width:{CANVAS_W}px; height:{CANVAS_H}px;"></div>
    <script>
        {js_literal}
    </script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var ch = Highcharts.charts[Highcharts.charts.length - 1];
            if (ch) {{
                ch.renderer.label(
                    '▶ Peak region: low-amplitude cycles near<br>' +
                    '  100 MPa mean stress dominate fatigue damage',
                    ch.plotLeft + ch.plotWidth * 0.55,
                    ch.plotTop + ch.plotHeight * 0.78
                ).css({{
                    fontSize: '28px',
                    color: '{ann_text}',
                    fontStyle: 'italic',
                    lineHeight: '40px'
                }}).attr({{
                    fill: '{ann_fill}',
                    stroke: '{ann_stroke}',
                    'stroke-width': 1.5,
                    padding: 18,
                    r: 8,
                    zIndex: 5
                }}).add();
            }}
        }});
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome — all four canvas-size knobs must agree
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
# CDP override is authoritative — --window-size alone loses ~139 px to Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride",
    {"width": CANVAS_W, "height": CANVAS_H, "deviceScaleFactor": 1, "mobile": False},
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dimensions — guards against ±1-2 px rounding in headless Chrome
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (CANVAS_W, CANVAS_H):
    _norm = Image.new("RGB", (CANVAS_W, CANVAS_H), PAGE_BG)
    _norm.paste(_img, ((CANVAS_W - _img.size[0]) // 2, (CANVAS_H - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
