""" pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: highcharts unknown | Python 3.14.3
Quality: 86/100 | Created: 2026-03-17
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

# Per-cluster EVM for color-coding storytelling
cluster_evm = np.zeros(16)
for idx in range(16):
    mask = symbol_indices == idx
    if np.any(mask):
        ei = received_i[mask] - ideal_i[idx]
        eq = received_q[mask] - ideal_q[idx]
        cluster_evm[idx] = np.sqrt(np.mean(ei**2 + eq**2)) / np.sqrt(signal_power) * 100

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings - square canvas for equal aspect ratio (required by spec)
chart.options.chart = {
    "type": "scatter",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#f8f9fa",
    "marginBottom": 280,
    "marginLeft": 240,
    "marginRight": 160,
    "marginTop": 200,
    "plotBorderWidth": 1,
    "plotBorderColor": "#dee2e6",
    "plotBackgroundColor": "#ffffff",
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"},
}

# Title with subtitle for signal parameters
chart.options.title = {
    "text": "16-QAM Constellation · scatter-constellation-diagram · highcharts · pyplots.ai",
    "style": {"fontSize": "40px", "fontWeight": "700", "color": "#1a1a2e", "letterSpacing": "0.3px"},
    "margin": 10,
}
chart.options.subtitle = {
    "text": f"SNR = {snr_db} dB  |  {num_symbols} received symbols  |  16 constellation points",
    "style": {"fontSize": "26px", "fontWeight": "400", "color": "#6c757d"},
    "y": 70,
}

# Axes with increased spacing for x-axis visibility
axis_limit = 5.0
decision_boundaries = [
    {
        "value": v,
        "color": "#adb5bd",
        "width": 2,
        "dashStyle": "Dash",
        "zIndex": 1,
        "label": {
            "text": f"d={v}" if v != 0 else "",
            "align": "right",
            "style": {"fontSize": "18px", "color": "#adb5bd"},
            "y": -6,
        },
    }
    for v in [-2, 0, 2]
]

# Zero-axis crosshair lines (solid, subtle)
zero_lines = [{"value": 0, "color": "#868e96", "width": 1.5, "zIndex": 2}]

chart.options.x_axis = {
    "title": {
        "text": "In-Phase (I)",
        "style": {"fontSize": "34px", "fontWeight": "600", "color": "#1a1a2e"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "22px", "color": "#495057"}, "y": 30},
    "min": -axis_limit,
    "max": axis_limit,
    "tickInterval": 1,
    "gridLineWidth": 0,
    "lineWidth": 2,
    "lineColor": "#495057",
    "tickWidth": 1,
    "tickLength": 10,
    "tickColor": "#495057",
    "plotLines": decision_boundaries + zero_lines,
}

chart.options.y_axis = {
    "title": {
        "text": "Quadrature (Q)",
        "style": {"fontSize": "34px", "fontWeight": "600", "color": "#1a1a2e"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "22px", "color": "#495057"}},
    "min": -axis_limit,
    "max": axis_limit,
    "tickInterval": 1,
    "gridLineWidth": 0,
    "lineWidth": 2,
    "lineColor": "#495057",
    "tickWidth": 1,
    "tickLength": 10,
    "tickColor": "#495057",
    "plotLines": decision_boundaries + zero_lines,
}

# Legend - positioned inside plot area at bottom-right to avoid clutter at top
chart.options.legend = {
    "enabled": True,
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "top",
    "floating": True,
    "x": -20,
    "y": 20,
    "backgroundColor": "rgba(255, 255, 255, 0.92)",
    "borderWidth": 1,
    "borderColor": "#dee2e6",
    "borderRadius": 8,
    "padding": 16,
    "shadow": {"enabled": True, "color": "rgba(0,0,0,0.06)", "offsetX": 2, "offsetY": 2, "width": 6},
    "itemStyle": {"fontSize": "26px", "fontWeight": "400", "color": "#343a40"},
    "symbolRadius": 8,
    "symbolHeight": 18,
    "symbolWidth": 18,
    "itemMarginTop": 6,
    "itemMarginBottom": 6,
}

# Received symbols series - color-coded by distance from ideal for storytelling
received_series = ScatterSeries()
received_series.name = "Received Symbols"
received_data = []
for j in range(num_symbols):
    dist = np.sqrt(error_i[j] ** 2 + error_q[j] ** 2)
    # Map distance to opacity: closer=lighter, farther=darker to highlight errors
    alpha = min(0.25 + 0.5 * (dist / (2 * noise_std)), 0.85)
    received_data.append(
        {"x": float(received_i[j]), "y": float(received_q[j]), "color": f"rgba(48, 105, 152, {alpha:.2f})"}
    )
received_series.data = received_data
received_series.color = "rgba(48, 105, 152, 0.45)"
received_series.marker = {"radius": 10, "symbol": "circle", "lineWidth": 0}
chart.add_series(received_series)

# Ideal constellation points series with prominent styling
ideal_series = ScatterSeries()
ideal_series.name = "Ideal Points"
ideal_series.data = [{"x": float(ideal_i[k]), "y": float(ideal_q[k])} for k in range(16)]
ideal_series.color = "#E67E22"
ideal_series.marker = {
    "radius": 20,
    "symbol": "diamond",
    "lineWidth": 3,
    "lineColor": "#C0392B",
    "fillColor": "#E67E22",
}
ideal_series.z_index = 10
chart.add_series(ideal_series)

# Disable credits
chart.options.credits = {"enabled": False}

# Plot options with custom tooltip using Highcharts formatter
chart.options.plot_options = {
    "scatter": {
        "tooltip": {"headerFormat": "", "pointFormat": "<b>{series.name}</b><br/>I: {point.x:.3f}<br/>Q: {point.y:.3f}"}
    },
    "series": {"animation": False, "turboThreshold": 2000},
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

# Custom JS for EVM annotation and signal quality indicator
custom_js = f"""
Highcharts.addEvent(Highcharts.Chart, 'load', function() {{
    var chart = this;
    var r = chart.renderer;

    // EVM metric box - upper left
    var evmGroup = r.g('evm-annotation').attr({{ zIndex: 12 }}).add();
    var boxX = chart.plotLeft + 30;
    var boxY = chart.plotTop + 25;

    r.rect(boxX, boxY, 340, 130, 8)
        .attr({{
            fill: 'rgba(255, 255, 255, 0.95)',
            stroke: '#1a1a2e',
            'stroke-width': 2,
            zIndex: 12
        }})
        .shadow({{ color: 'rgba(0,0,0,0.08)', offsetX: 3, offsetY: 3, width: 8 }})
        .add(evmGroup);

    r.text('EVM = {evm:.1f}%', boxX + 24, boxY + 48)
        .css({{ fontSize: '36px', fontWeight: '700', color: '#1a1a2e' }})
        .add(evmGroup);

    r.text('SNR = {snr_db} dB', boxX + 24, boxY + 100)
        .css({{ fontSize: '28px', fontWeight: '400', color: '#6c757d' }})
        .add(evmGroup);

    // Quality indicator bar under EVM
    var barX = boxX + 24;
    var barY = boxY + 112;
    var barW = 290;
    var evmPct = Math.min({evm:.1f} / 30, 1);  // normalize to 0-30% range
    var barColor = evmPct < 0.33 ? '#2ecc71' : evmPct < 0.66 ? '#f39c12' : '#e74c3c';

    r.rect(barX, barY, barW, 6, 3)
        .attr({{ fill: '#e9ecef', zIndex: 12 }})
        .add(evmGroup);

    r.rect(barX, barY, barW * evmPct, 6, 3)
        .attr({{ fill: barColor, zIndex: 13 }})
        .add(evmGroup);
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
    <div id="container" style="width: 3600px; height: 3600px;"></div>
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
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
