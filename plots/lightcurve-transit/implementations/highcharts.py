""" pyplots.ai
lightcurve-transit: Astronomical Light Curve
Library: highcharts unknown | Python 3.14.3
Quality: 82/100 | Created: 2026-03-18
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Simulated exoplanet transit (phase-folded)
np.random.seed(42)

n_points = 400
phase = np.sort(np.random.uniform(0.0, 1.0, n_points))

# Transit model parameters
transit_center = 0.5
transit_depth = 0.01
half_duration = 0.04
ingress_width = 0.012


# Smooth transit model using tanh for ingress/egress
def transit_model(phases):
    result = np.ones_like(phases)
    dist = np.abs(phases - transit_center)
    # Smooth ingress/egress using hyperbolic tangent
    ingress = 0.5 * (1.0 + np.tanh((half_duration - dist) / ingress_width))
    # Limb darkening: slightly rounded bottom
    limb = 1.0 - 0.15 * (dist / half_duration) ** 2
    limb = np.clip(limb, 0.85, 1.0)
    result = 1.0 - transit_depth * ingress * limb
    return result


model_flux = transit_model(phase)

# Observed flux with noise
flux_err = np.random.uniform(0.001, 0.003, n_points)
flux = model_flux + np.random.normal(0, 1, n_points) * flux_err

# Prepare scatter data with error bars: [x, y]
scatter_data = [[round(float(p), 5), round(float(f), 6)] for p, f in zip(phase, flux, strict=True)]

# Error bar data: [x, low, high]
errorbar_data = [
    [round(float(p), 5), round(float(f - e), 6), round(float(f + e), 6)]
    for p, f, e in zip(phase, flux, flux_err, strict=True)
]

# Model curve (smooth, denser sampling)
model_phase = np.linspace(0.0, 1.0, 500)
model_curve = transit_model(model_phase)

model_data = [[round(float(p), 5), round(float(f), 6)] for p, f in zip(model_phase, model_curve, strict=True)]

# Chart options
chart_options = {
    "chart": {
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "style": {"fontFamily": "Arial, sans-serif"},
        "spacingTop": 60,
        "spacingBottom": 80,
        "spacingLeft": 60,
        "spacingRight": 60,
    },
    "title": {
        "text": "lightcurve-transit \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "58px", "fontWeight": "bold"},
    },
    "subtitle": {
        "text": "Phase-folded exoplanet transit with quadratic limb darkening model",
        "style": {"fontSize": "34px", "color": "#666666"},
    },
    "xAxis": {
        "title": {"text": "Orbital Phase", "style": {"fontSize": "42px"}},
        "labels": {"style": {"fontSize": "32px"}, "format": "{value:.1f}"},
        "min": 0.0,
        "max": 1.0,
        "tickInterval": 0.1,
        "gridLineWidth": 0,
        "lineWidth": 2,
        "lineColor": "#333333",
    },
    "yAxis": {
        "title": {"text": "Relative Flux", "style": {"fontSize": "42px"}},
        "labels": {"style": {"fontSize": "32px"}, "format": "{value:.4f}"},
        "gridLineColor": "#e8e8e8",
        "gridLineWidth": 1,
        "gridLineDashStyle": "Dot",
        "lineWidth": 2,
        "lineColor": "#333333",
    },
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "x": -40,
        "y": 80,
        "itemStyle": {"fontSize": "32px"},
        "itemMarginBottom": 10,
    },
    "tooltip": {
        "headerFormat": "<b>Phase: {point.x:.4f}</b><br/>",
        "pointFormat": "Flux: {point.y:.5f}",
        "style": {"fontSize": "24px"},
    },
    "plotOptions": {
        "scatter": {"marker": {"radius": 5, "lineWidth": 1, "lineColor": "#ffffff"}},
        "errorbar": {"lineWidth": 2, "whiskerLength": 0, "stemWidth": 2, "color": "rgba(48, 105, 152, 0.25)"},
        "line": {"lineWidth": 4, "marker": {"enabled": False}},
    },
    "series": [
        {
            "name": "Observed Flux",
            "type": "scatter",
            "data": scatter_data,
            "color": "#306998",
            "marker": {"symbol": "circle"},
            "zIndex": 2,
        },
        {"name": "Measurement Error", "type": "errorbar", "data": errorbar_data, "zIndex": 1, "showInLegend": True},
        {"name": "Transit Model", "type": "line", "data": model_data, "color": "#d4513d", "zIndex": 3},
    ],
    "credits": {"enabled": False},
}

# Download Highcharts JS and highcharts-more (needed for errorbar)
js_urls = [
    ("https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"),
    ("https://code.highcharts.com/highcharts-more.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js"),
]
js_parts = []
for primary, fallback in js_urls:
    for url in (primary, fallback):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                js_parts.append(response.read().decode("utf-8"))
            break
        except Exception:
            continue
all_js = "\n".join(js_parts)

# Generate HTML with inline scripts
chart_options_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{all_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4900, 2900)
driver.get(f"file://{temp_path}")
time.sleep(5)

driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700
img = Image.open("plot_raw.png")
final_img = Image.new("RGB", (4800, 2700), (255, 255, 255))
final_img.paste(img.crop((0, 0, min(img.width, 4800), min(img.height, 2700))), (0, 0))
final_img.save("plot.png")

# Clean up
Path("plot_raw.png").unlink()
Path(temp_path).unlink()
