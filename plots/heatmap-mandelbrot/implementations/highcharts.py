""" pyplots.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: highcharts unknown | Python 3.14.3
Quality: 87/100 | Created: 2026-03-03
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Mandelbrot set on the complex plane
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
max_iter = 100
nx, ny = 350, 250

real = np.linspace(x_min, x_max, nx)
imag = np.linspace(y_min, y_max, ny)
col_size = round((x_max - x_min) / nx, 6)
row_size = round((y_max - y_min) / ny, 6)

# Vectorized Mandelbrot iteration with smooth coloring
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

# Log-scale iteration counts for better color distribution across the boundary
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

# Layout - preserve complex plane aspect ratio (3.5 : 2.5)
chart_w, chart_h = 4800, 2700
m_top, m_bottom, m_left = 120, 160, 220
plot_h = chart_h - m_top - m_bottom
data_ratio = (x_max - x_min) / (y_max - y_min)
plot_w = int(plot_h * data_ratio)
m_right = chart_w - plot_w - m_left

# Chart configuration
chart_options = {
    "chart": {
        "type": "heatmap",
        "width": chart_w,
        "height": chart_h,
        "backgroundColor": "#0a0a1a",
        "marginTop": m_top,
        "marginBottom": m_bottom,
        "marginLeft": m_left,
        "marginRight": m_right,
        "style": {"fontFamily": "'Segoe UI', Roboto, Arial, sans-serif"},
    },
    "title": {
        "text": "heatmap-mandelbrot \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "600", "color": "#e0e0f0"},
        "y": 40,
    },
    "xAxis": {
        "title": {"text": "Real Axis (Re)", "style": {"fontSize": "30px", "color": "#b0b0c8"}, "margin": 20},
        "labels": {"style": {"fontSize": "24px", "color": "#8888a8"}},
        "min": x_min,
        "max": x_max,
        "startOnTick": False,
        "endOnTick": False,
        "tickInterval": 0.5,
        "lineColor": "#333355",
        "tickColor": "#333355",
        "gridLineWidth": 0,
    },
    "yAxis": {
        "title": {"text": "Imaginary Axis (Im)", "style": {"fontSize": "30px", "color": "#b0b0c8"}, "margin": 20},
        "labels": {"style": {"fontSize": "24px", "color": "#8888a8"}, "format": "{value}i"},
        "min": y_min,
        "max": y_max,
        "startOnTick": False,
        "endOnTick": False,
        "tickInterval": 0.5,
        "lineColor": "#333355",
        "tickColor": "#333355",
        "gridLineWidth": 0,
    },
    "colorAxis": {
        "min": 0,
        "max": max_log,
        "stops": [
            [0, "#0d0887"],
            [0.13, "#46039f"],
            [0.25, "#7201a8"],
            [0.38, "#9c179e"],
            [0.50, "#bd3786"],
            [0.63, "#d8576b"],
            [0.75, "#ed7953"],
            [0.88, "#fbae52"],
            [1.0, "#f0f921"],
        ],
        "tickPositions": [round(float(np.log(v + 1)), 2) for v in [0, 5, 10, 20, 50, 100]],
        "labels": {"style": {"fontSize": "22px", "color": "#8888a8"}},
    },
    "legend": {
        "title": {"text": "Escape Iterations", "style": {"fontSize": "26px", "fontWeight": "600", "color": "#b0b0c8"}},
        "align": "right",
        "layout": "vertical",
        "verticalAlign": "middle",
        "symbolHeight": 900,
        "symbolWidth": 30,
        "itemStyle": {"fontSize": "22px", "color": "#8888a8"},
        "x": -200,
    },
    "tooltip": {"style": {"fontSize": "24px"}, "useHTML": True},
    "credits": {"enabled": False},
    "series": [
        {
            "type": "heatmap",
            "name": "Mandelbrot",
            "data": heatmap_data,
            "colsize": col_size,
            "rowsize": row_size,
            "nullColor": "#000000",
            "borderWidth": 0,
            "turboThreshold": 0,
        }
    ],
}

# Download Highcharts JS and heatmap module
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
heatmap_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/heatmap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

options_json = json.dumps(chart_options)

# HTML with inline scripts and custom formatters
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:#0a0a1a;">
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

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot using headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2840")
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--hide-scrollbars")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4800, 2840)
driver.get(f"file://{temp_path}")
time.sleep(8)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
