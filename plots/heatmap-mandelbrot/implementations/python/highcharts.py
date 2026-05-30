""" anyplot.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-30
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Data - Mandelbrot set on the complex plane
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
max_iter = 100
nx, ny = 800, 600

real = np.linspace(x_min, x_max, nx)
imag = np.linspace(y_min, y_max, ny)
col_size = round((x_max - x_min) / nx * 1.01, 6)
row_size = round((y_max - y_min) / ny * 1.01, 6)

# Vectorized Mandelbrot iteration with smooth coloring (log2-based normalized iteration count)
c = real[np.newaxis, :] + 1j * imag[:, np.newaxis]
z = np.zeros_like(c)
smooth_iter = np.full((ny, nx), -1.0)
mask = np.ones((ny, nx), dtype=bool)

for i in range(max_iter):
    z[mask] = z[mask] ** 2 + c[mask]
    escaped = mask & (np.abs(z) > 2)
    if np.any(escaped):
        abs_z = np.abs(z[escaped])
        log_zn = np.log2(np.maximum(abs_z, 2.0))
        smooth = np.log2(np.maximum(log_zn, 1.0))
        smooth_iter[escaped] = np.maximum(i + 1.0 - smooth, 0.0)
    mask &= ~escaped

# Log-scale transformation for better color distribution across the fractal boundary
exterior = smooth_iter >= 0
smooth_iter[exterior] = np.log(smooth_iter[exterior] + 1)
max_log = float(np.log(max_iter + 1))

# Build heatmap data [real, imaginary, log_iteration_count]
real_r = [round(float(v), 4) for v in real]
imag_r = [round(float(v), 4) for v in imag]
heatmap_data = [
    [real_r[xi], imag_r[yi], None if smooth_iter[yi, xi] < 0 else round(float(smooth_iter[yi, xi]), 2)]
    for yi in range(ny)
    for xi in range(nx)
]

# Canvas - 3200x1800 (landscape, natural for the 7:5 complex plane proportion)
chart_w, chart_h = 3200, 1800
title = "heatmap-mandelbrot · python · highcharts · anyplot.ai"

chart_options = {
    "chart": {
        "type": "heatmap",
        "width": chart_w,
        "height": chart_h,
        "backgroundColor": PAGE_BG,
        "marginTop": 80,
        "marginBottom": 160,
        "marginLeft": 160,
        "marginRight": 240,
        "style": {"fontFamily": "'Segoe UI', Roboto, Arial, sans-serif"},
        "plotBorderWidth": 0,
    },
    "title": {"text": title, "style": {"fontSize": "66px", "fontWeight": "600", "color": INK}, "y": 52},
    "xAxis": {
        "title": {"text": "Real Axis (Re)", "style": {"fontSize": "56px", "color": INK}, "margin": 16},
        "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
        "min": x_min,
        "max": x_max,
        "startOnTick": False,
        "endOnTick": False,
        "tickInterval": 0.5,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineWidth": 0,
    },
    "yAxis": {
        "title": {"text": "Imaginary Axis (Im)", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
        "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "{value}i"},
        "min": y_min,
        "max": y_max,
        "startOnTick": False,
        "endOnTick": False,
        "tickInterval": 0.5,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineWidth": 0,
    },
    "colorAxis": {
        "min": 0,
        "max": max_log,
        "stops": [[0, "#009E73"], [1, "#4467A3"]],
        "tickPositions": [round(float(np.log(v + 1)), 2) for v in [0, 5, 10, 20, 50, 100]],
        "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    },
    "legend": {
        "title": {"text": "Escape Iterations", "style": {"fontSize": "40px", "fontWeight": "600", "color": INK}},
        "align": "right",
        "layout": "vertical",
        "verticalAlign": "middle",
        "symbolHeight": 1200,
        "symbolWidth": 28,
        "itemStyle": {"fontSize": "36px", "color": INK_SOFT},
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "x": -10,
    },
    "tooltip": {"style": {"fontSize": "36px"}, "useHTML": True},
    "credits": {"enabled": False},
    "series": [
        {
            "type": "heatmap",
            "name": "Mandelbrot",
            "data": heatmap_data,
            "colsize": col_size,
            "rowsize": row_size,
            "nullColor": "#0a0a0a",
            "borderWidth": 0,
            "turboThreshold": 0,
        }
    ],
}

# Download Highcharts JS and heatmap module inline (required for headless Chrome)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
heatmap_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/heatmap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

options_json = json.dumps(chart_options)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:{PAGE_BG};">
    <div id="container" style="width:{chart_w}px; height:{chart_h}px;"></div>
    <script>
        var opts = {options_json};
        opts.colorAxis.labels.formatter = function() {{
            return Math.round(Math.exp(this.value) - 1);
        }};
        opts.tooltip.formatter = function() {{
            var x = this.point.x.toFixed(3);
            var y = this.point.y.toFixed(3);
            var sign = this.point.y >= 0 ? '+' : '';
            var iter = this.point.value !== null
                ? Math.round(Math.exp(this.point.value) - 1)
                : '\\u221e (inside set)';
            return '<b>c = ' + x + ' ' + sign + y + 'i</b><br>'
                 + 'Iterations: <b>' + iter + '</b>';
        }};
        Highcharts.chart('container', opts);
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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

_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
