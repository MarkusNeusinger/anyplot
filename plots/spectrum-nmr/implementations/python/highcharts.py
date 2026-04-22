""" pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: highcharts unknown | Python 3.14.3
Quality: 90/100 | Created: 2026-03-09
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - synthetic 1H NMR spectrum of ethanol (CH3CH2OH)
np.random.seed(42)

chemical_shift = np.linspace(0, 12, 6000)

intensity = np.zeros_like(chemical_shift)
x = chemical_shift
w = 0.012  # peak width for multiplets

# Lorentzian peak shape: a * w^2 / ((x - c)^2 + w^2)
# TMS reference peak at 0 ppm (singlet, narrower)
intensity += 0.3 * 0.008**2 / ((x - 0.0) ** 2 + 0.008**2)

# CH3 triplet near 1.18 ppm (3 peaks, 1:2:1 pattern)
ch3_center = 1.18
j_coupling = 0.07
intensity += 0.65 * w**2 / ((x - (ch3_center - j_coupling)) ** 2 + w**2)
intensity += 1.30 * w**2 / ((x - ch3_center) ** 2 + w**2)
intensity += 0.65 * w**2 / ((x - (ch3_center + j_coupling)) ** 2 + w**2)

# CH2 quartet near 3.69 ppm (4 peaks, 1:3:3:1 pattern)
ch2_center = 3.69
intensity += 0.22 * w**2 / ((x - (ch2_center - 1.5 * j_coupling)) ** 2 + w**2)
intensity += 0.66 * w**2 / ((x - (ch2_center - 0.5 * j_coupling)) ** 2 + w**2)
intensity += 0.66 * w**2 / ((x - (ch2_center + 0.5 * j_coupling)) ** 2 + w**2)
intensity += 0.22 * w**2 / ((x - (ch2_center + 1.5 * j_coupling)) ** 2 + w**2)

# OH singlet near 2.61 ppm (slightly broader)
intensity += 0.40 * 0.015**2 / ((x - 2.61) ** 2 + 0.015**2)

# Add slight baseline noise
intensity += np.random.normal(0, 0.003, len(chemical_shift))
intensity = np.clip(intensity, 0, None)

# Prepare data for Highcharts (reversed x-axis: high ppm on left)
spectrum_data = [
    [round(float(chemical_shift[i]), 4), round(float(intensity[i]), 5)] for i in range(len(chemical_shift))
]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "spacingTop": 60,
    "spacingBottom": 80,
    "spacingLeft": 80,
    "spacingRight": 100,
    "plotBorderWidth": 0,
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "Ethanol \u00b9H NMR \u00b7 spectrum-nmr \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "52px", "fontWeight": "600", "color": "#2c3e50"},
    "margin": 50,
}

chart.options.subtitle = {
    "text": "CH\u2083CH\u2082OH in CDCl\u2083 (400 MHz)",
    "style": {"fontSize": "32px", "fontWeight": "400", "color": "#7f8c8d"},
    "y": 90,
}

# X-axis: chemical shift (ppm) - REVERSED (high ppm on left)
chart.options.x_axis = {
    "title": {
        "text": "Chemical Shift (ppm)",
        "style": {"fontSize": "36px", "fontWeight": "600", "color": "#2c3e50"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#666666"}},
    "reversed": True,
    "min": -0.5,
    "max": 5.5,
    "tickInterval": 0.5,
    "gridLineWidth": 0,
    "lineColor": "#34495e",
    "lineWidth": 2,
    "tickWidth": 2,
    "tickLength": 8,
    "tickColor": "#34495e",
}

# Y-axis: intensity (tightened range to reduce whitespace above peaks)
chart.options.y_axis = {
    "title": {
        "text": "Intensity (a.u.)",
        "style": {"fontSize": "36px", "fontWeight": "600", "color": "#2c3e50"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#666666"}},
    "min": 0,
    "max": 1.42,
    "gridLineColor": "#e8e8e8",
    "gridLineDashStyle": "Dot",
    "gridLineWidth": 1,
    "lineColor": "#34495e",
    "lineWidth": 2,
    "tickWidth": 2,
    "tickLength": 8,
    "tickColor": "#34495e",
    "opposite": False,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "enabled": True,
    "headerFormat": "",
    "pointFormat": "\u03b4 = {point.x:.2f} ppm<br/>Intensity: {point.y:.4f}",
    "style": {"fontSize": "24px"},
    "borderRadius": 8,
}

chart.options.plot_options = {
    "series": {"animation": False, "states": {"hover": {"lineWidthPlus": 0}}},
    "line": {"lineWidth": 2, "marker": {"enabled": False}, "turboThreshold": 10000},
}

# Annotations for peak labels with subtle connector lines
chart.options.annotations = [
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": "rgba(255,255,255,0.85)",
            "borderWidth": 0,
            "borderRadius": 6,
            "padding": 10,
            "style": {"fontSize": "30px", "color": "#306998", "fontWeight": "600"},
            "shape": "connector",
        },
        "labels": [
            {"point": {"x": 0.0, "y": 0.3, "xAxis": 0, "yAxis": 0}, "text": "TMS<br>\u03b4 0.00", "y": -50, "x": 10},
            {
                "point": {"x": 1.18, "y": 1.30, "xAxis": 0, "yAxis": 0},
                "text": "CH\u2083 (triplet)<br>\u03b4 1.18",
                "y": -50,
            },
            {"point": {"x": 2.61, "y": 0.40, "xAxis": 0, "yAxis": 0}, "text": "OH (singlet)<br>\u03b4 2.61", "y": -55},
            {
                "point": {"x": 3.69, "y": 0.66, "xAxis": 0, "yAxis": 0},
                "text": "CH\u2082 (quartet)<br>\u03b4 3.69",
                "y": -55,
            },
        ],
    }
]

# Add spectrum series
series = LineSeries()
series.data = spectrum_data
series.name = "Ethanol \u00b9H NMR"
series.color = "#306998"
chart.add_series(series)

# Save HTML
html_str = chart.to_js_literal()

js_urls = {
    "highcharts": "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js",
    "annotations": "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js",
}
js_scripts = {}
for name, url in js_urls.items():
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        js_scripts[name] = response.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_scripts["highcharts"]}</script>
    <script>{js_scripts["annotations"]}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
