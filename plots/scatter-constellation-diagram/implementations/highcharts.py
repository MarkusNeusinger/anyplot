"""pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-03-17
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - 16-QAM constellation
np.random.seed(42)

# Ideal 16-QAM constellation points on a 4x4 grid at +/-1, +/-3
ideal_levels = [-3, -1, 1, 3]
ideal_i = np.array([i for i in ideal_levels for _ in ideal_levels])
ideal_q = np.array([q for _ in ideal_levels for q in ideal_levels])

# Generate received symbols with additive Gaussian noise (~20 dB SNR)
num_symbols = 1000
symbol_indices = np.random.randint(0, 16, num_symbols)
snr_db = 20
signal_power = np.mean(ideal_i**2 + ideal_q**2)
noise_std = np.sqrt(signal_power / (10 ** (snr_db / 10)))

received_i = ideal_i[symbol_indices] + np.random.normal(0, noise_std, num_symbols)
received_q = ideal_q[symbol_indices] + np.random.normal(0, noise_std, num_symbols)

# Calculate EVM (Error Vector Magnitude)
error_i = received_i - ideal_i[symbol_indices]
error_q = received_q - ideal_q[symbol_indices]
evm = np.sqrt(np.mean(error_i**2 + error_q**2)) / np.sqrt(signal_power) * 100

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 200,
    "marginRight": 150,
    "marginTop": 150,
}

# Title
chart.options.title = {
    "text": "16-QAM Constellation · scatter-constellation-diagram · highcharts · pyplots.ai",
    "style": {"fontSize": "44px", "fontWeight": "bold"},
}

# Axes
axis_limit = 5.0
chart.options.x_axis = {
    "title": {"text": "In-Phase (I)", "style": {"fontSize": "36px"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px"}},
    "min": -axis_limit,
    "max": axis_limit,
    "tickInterval": 1,
    "gridLineWidth": 0,
    "lineWidth": 2,
    "lineColor": "#333333",
}

chart.options.y_axis = {
    "title": {"text": "Quadrature (Q)", "style": {"fontSize": "36px"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px"}},
    "min": -axis_limit,
    "max": axis_limit,
    "tickInterval": 1,
    "gridLineWidth": 0,
    "lineWidth": 2,
    "lineColor": "#333333",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "middle",
    "itemStyle": {"fontSize": "28px"},
    "symbolRadius": 8,
    "itemMarginTop": 10,
}

# Received symbols series
received_series = ScatterSeries()
received_series.name = "Received Symbols"
received_series.data = [{"x": float(received_i[j]), "y": float(received_q[j])} for j in range(num_symbols)]
received_series.color = "rgba(48, 105, 152, 0.35)"
received_series.marker = {"radius": 6, "symbol": "circle"}
chart.add_series(received_series)

# Ideal constellation points series
ideal_series = ScatterSeries()
ideal_series.name = "Ideal Points"
ideal_series.data = [{"x": float(ideal_i[k]), "y": float(ideal_q[k])} for k in range(16)]
ideal_series.color = "#E74C3C"
ideal_series.marker = {"radius": 18, "symbol": "diamond", "lineWidth": 4, "lineColor": "#E74C3C"}
chart.add_series(ideal_series)

# Plot options
chart.options.plot_options = {
    "scatter": {
        "tooltip": {"headerFormat": "", "pointFormat": "<b>{series.name}</b><br>I: {point.x:.3f}, Q: {point.y:.3f}"}
    },
    "series": {"animation": False},
}

# Download Highcharts JS
js_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
highcharts_js = ""
for url in js_urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue

# Generate JS literal
html_str = chart.to_js_literal()

# Custom JS for decision boundaries and EVM annotation
custom_js = f"""
Highcharts.addEvent(Highcharts.Chart, 'load', function() {{
    var chart = this;
    var renderer = chart.renderer;
    var xAxis = chart.xAxis[0];
    var yAxis = chart.yAxis[0];

    // Decision boundary lines (at +/-2, 0 on both axes)
    var boundaries = [-2, 0, 2];
    boundaries.forEach(function(val) {{
        // Vertical decision boundaries
        var x = xAxis.toPixels(val);
        var yTop = yAxis.toPixels({axis_limit});
        var yBot = yAxis.toPixels(-{axis_limit});
        renderer.path(['M', x, yTop, 'L', x, yBot])
            .attr({{
                stroke: '#aaaaaa',
                'stroke-width': 2,
                'stroke-dasharray': '12,8',
                zIndex: 1
            }})
            .add();

        // Horizontal decision boundaries
        var y = yAxis.toPixels(val);
        var xLeft = xAxis.toPixels(-{axis_limit});
        var xRight = xAxis.toPixels({axis_limit});
        renderer.path(['M', xLeft, y, 'L', xRight, y])
            .attr({{
                stroke: '#aaaaaa',
                'stroke-width': 2,
                'stroke-dasharray': '12,8',
                zIndex: 1
            }})
            .add();
    }});

    // EVM annotation
    renderer.label('EVM = {evm:.1f}%', chart.plotLeft + 40, chart.plotTop + 40)
        .attr({{
            fill: 'rgba(255, 255, 255, 0.85)',
            stroke: '#333333',
            'stroke-width': 2,
            padding: 18,
            r: 8,
            zIndex: 12
        }})
        .css({{
            fontSize: '34px',
            fontWeight: 'bold',
            color: '#333333'
        }})
        .add();
}});
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{custom_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
