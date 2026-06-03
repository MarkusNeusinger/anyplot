""" anyplot.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-06-03
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
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
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — first series always #009E73
BRAND = "#009E73"

# Data — synthetic 1H NMR spectrum of ethanol (CH3CH2OH)
np.random.seed(42)

chemical_shift = np.linspace(0, 12, 6000)
intensity = np.zeros_like(chemical_shift)
x = chemical_shift
w = 0.012  # Lorentzian peak half-width for multiplets

# TMS reference peak at 0 ppm (singlet, narrower)
intensity += 0.3 * 0.008**2 / ((x - 0.0) ** 2 + 0.008**2)

# CH3 triplet near 1.18 ppm (1:2:1 pattern)
ch3_center = 1.18
j_coupling = 0.07
intensity += 0.65 * w**2 / ((x - (ch3_center - j_coupling)) ** 2 + w**2)
intensity += 1.30 * w**2 / ((x - ch3_center) ** 2 + w**2)
intensity += 0.65 * w**2 / ((x - (ch3_center + j_coupling)) ** 2 + w**2)

# CH2 quartet near 3.69 ppm (1:3:3:1 pattern)
ch2_center = 3.69
intensity += 0.22 * w**2 / ((x - (ch2_center - 1.5 * j_coupling)) ** 2 + w**2)
intensity += 0.66 * w**2 / ((x - (ch2_center - 0.5 * j_coupling)) ** 2 + w**2)
intensity += 0.66 * w**2 / ((x - (ch2_center + 0.5 * j_coupling)) ** 2 + w**2)
intensity += 0.22 * w**2 / ((x - (ch2_center + 1.5 * j_coupling)) ** 2 + w**2)

# OH singlet near 2.61 ppm (slightly broader)
intensity += 0.40 * 0.015**2 / ((x - 2.61) ** 2 + 0.015**2)

# Slight baseline noise
intensity += np.random.normal(0, 0.003, len(chemical_shift))
intensity = np.clip(intensity, 0, None)

spectrum_data = [
    [round(float(chemical_shift[i]), 4), round(float(intensity[i]), 5)] for i in range(len(chemical_shift))
]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

title = "Ethanol ¹H NMR · spectrum-nmr · python · highcharts · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = f"{max(44, round(66 * ratio))}px"

chart.options.chart = {
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 140,
    "spacingTop": 40,
    "spacingLeft": 60,
    "spacingRight": 60,
    "plotBorderWidth": 0,
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif", "color": INK},
}

chart.options.title = {
    "text": title,
    "style": {"fontSize": title_fontsize, "fontWeight": "600", "color": INK},
    "margin": 30,
}

chart.options.subtitle = {
    "text": "CH₃CH₂OH in CDCl₃ (400 MHz)",
    "style": {"fontSize": "40px", "fontWeight": "400", "color": INK_SOFT},
}

# X-axis: chemical shift (ppm) — REVERSED (high ppm on left, standard NMR convention)
chart.options.x_axis = {
    "title": {
        "text": "Chemical Shift (ppm)",
        "style": {"fontSize": "56px", "fontWeight": "600", "color": INK},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "reversed": True,
    "min": -0.5,
    "max": 5.5,
    "tickInterval": 0.5,
    "gridLineWidth": 0,
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "tickWidth": 1,
    "tickLength": 8,
    "tickColor": INK_SOFT,
    # Emphasize the dominant CH3 triplet region with a subtle highlight band
    "plotBands": [
        {
            "from": 0.97,
            "to": 1.39,
            "color": "rgba(0,158,115,0.07)",
            "zIndex": 1,
            "label": {
                "text": "dominant",
                "style": {"fontSize": "34px", "color": INK_MUTED, "fontStyle": "italic"},
                "verticalAlign": "top",
                "y": 20,
            },
        }
    ],
}

# Y-axis: intensity — max 1.35 gives ~4% headroom above tallest peak (1.30)
chart.options.y_axis = {
    "title": {
        "text": "Intensity (a.u.)",
        "style": {"fontSize": "56px", "fontWeight": "600", "color": INK},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": 0,
    "max": 1.35,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "gridLineWidth": 1,
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "tickWidth": 1,
    "tickLength": 8,
    "tickColor": INK_SOFT,
    "opposite": False,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "enabled": True,
    "headerFormat": "",
    "pointFormat": "δ = {point.x:.2f} ppm<br/>Intensity: {point.y:.4f}",
    "borderRadius": 8,
    "backgroundColor": ELEVATED_BG,
    "style": {"fontSize": "36px", "color": INK},
}

chart.options.plot_options = {
    "series": {"animation": False, "states": {"hover": {"lineWidthPlus": 0}}},
    "area": {"lineWidth": 2, "marker": {"enabled": False}, "turboThreshold": 10000},
}

# Peak annotations with connector lines (requires annotations.js module)
chart.options.annotations = [
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": ELEVATED_BG,
            "borderWidth": 0,
            "borderRadius": 6,
            "padding": 10,
            "style": {"fontSize": "40px", "color": INK_MUTED, "fontWeight": "600"},
            "shape": "connector",
        },
        "labels": [
            {"point": {"x": 0.0, "y": 0.3, "xAxis": 0, "yAxis": 0}, "text": "TMS<br>δ 0.00", "y": -50, "x": 10},
            {"point": {"x": 1.18, "y": 1.30, "xAxis": 0, "yAxis": 0}, "text": "CH₃ (triplet)<br>δ 1.18", "y": -50},
            {"point": {"x": 2.61, "y": 0.40, "xAxis": 0, "yAxis": 0}, "text": "OH (singlet)<br>δ 2.61", "y": -55},
            {"point": {"x": 3.69, "y": 0.66, "xAxis": 0, "yAxis": 0}, "text": "CH₂ (quartet)<br>δ 3.69", "y": -55},
        ],
    }
]

series = AreaSeries()
series.data = spectrum_data
series.name = "Ethanol ¹H NMR"
series.color = BRAND
series.fill_color = "rgba(0,158,115,0.12)"
series.fill_opacity = 1
chart.add_series(series)

# Export — download Highcharts + annotations module for inline embedding
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
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome — CDP override is authoritative for exact viewport dims
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

# Belt-and-braces: pin to exact canvas dims in case of ±1-2 px rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
