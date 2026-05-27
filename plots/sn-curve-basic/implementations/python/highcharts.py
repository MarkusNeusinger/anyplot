""" anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-20
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"  # Okabe-Ito #1 — test data scatter
FIT_COLOR = "#C475FD"  # Okabe-Ito #2 — Basquin fit line

# Data: Simulated fatigue test results for structural steel specimens
np.random.seed(42)

stress_levels = np.array([450, 400, 350, 320, 300, 280, 260, 250, 240, 230, 220, 210])

cycles_data = []
stress_data = []

for stress_val in stress_levels:
    A = 1200
    b = 0.12
    N_mean = (stress_val / A) ** (-1 / b)
    n_samples = np.random.randint(2, 5)
    for _ in range(n_samples):
        scatter = np.exp(np.random.normal(0, 0.3))
        cycles_data.append(N_mean * scatter)
        stress_data.append(stress_val + np.random.normal(0, 5))

cycles = np.array(cycles_data)
stress = np.array(stress_data)

# Basquin equation fit (log-linear regression)
log_cycles = np.log10(cycles)
log_stress = np.log10(stress)
coeffs = np.polyfit(log_cycles, log_stress, 1)
fit_cycles = np.logspace(2, 8, 100)
fit_stress = 10 ** (coeffs[0] * np.log10(fit_cycles) + coeffs[1])

# Material reference properties for structural steel
ultimate_strength = 500
yield_strength = 350
endurance_limit = 200

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    "marginBottom": 140,
    "marginLeft": 160,
    "marginRight": 80,
    "marginTop": 110,
    "plotBorderWidth": 0,
}

chart.options.title = {
    "text": "sn-curve-basic · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": "Structural Steel — Power-law (Basquin) regression with fatigue regime boundaries",
    "style": {"fontSize": "40px", "color": INK_SOFT},
    "margin": 30,
}

region_bands = [
    {
        "from": 100,
        "to": 10000,
        "color": "rgba(196, 117, 253, 0.07)",
        "label": {
            "text": "Low-Cycle Fatigue",
            "style": {"fontSize": "36px", "color": INK_SOFT},
            "align": "center",
            "verticalAlign": "top",
            "y": 30,
        },
    },
    {
        "from": 10000,
        "to": 1000000,
        "color": "rgba(68, 103, 163, 0.05)",
        "label": {
            "text": "High-Cycle Fatigue",
            "style": {"fontSize": "36px", "color": INK_SOFT},
            "align": "center",
            "verticalAlign": "top",
            "y": 30,
        },
    },
    {
        "from": 1000000,
        "to": 100000000,
        "color": "rgba(0,158,115,0.06)",
        "label": {
            "text": "Infinite Life",
            "style": {"fontSize": "36px", "color": INK_SOFT},
            "align": "center",
            "verticalAlign": "top",
            "y": 30,
        },
    },
]

chart.options.x_axis = {
    "type": "logarithmic",
    "title": {"text": "Number of Cycles to Failure (N)", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": 100,
    "max": 100000000,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineWidth": 1,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "tickWidth": 1,
    "tickInterval": 1,
    "plotBands": region_bands,
}

chart.options.y_axis = {
    "type": "logarithmic",
    "title": {"text": "Stress Amplitude (MPa)", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": 150,
    "max": 600,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineWidth": 1,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "tickWidth": 1,
    "plotLines": [
        {
            "value": ultimate_strength,
            "color": "#BD8233",
            "width": 4,
            "dashStyle": "Dash",
            "label": {
                "text": f"Ultimate Strength ({ultimate_strength} MPa)",
                "align": "left",
                "style": {"fontSize": "34px", "color": "#BD8233", "fontWeight": "bold"},
                "x": 10,
                "y": -10,
            },
            "zIndex": 3,
        },
        {
            "value": yield_strength,
            "color": "#AE3030",
            "width": 4,
            "dashStyle": "Dash",
            "label": {
                "text": f"Yield Strength ({yield_strength} MPa)",
                "align": "left",
                "style": {"fontSize": "34px", "color": "#AE3030", "fontWeight": "bold"},
                "x": 10,
                "y": -10,
            },
            "zIndex": 3,
        },
        {
            "value": endurance_limit,
            "color": "#2ABCCD",
            "width": 4,
            "dashStyle": "Dash",
            "label": {
                "text": f"Endurance Limit ({endurance_limit} MPa)",
                "align": "left",
                "style": {"fontSize": "34px", "color": "#2ABCCD", "fontWeight": "bold"},
                "x": 10,
                "y": -10,
            },
            "zIndex": 3,
        },
    ],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "44px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 160,
}

chart.options.plot_options = {
    "scatter": {
        "marker": {"radius": 10, "symbol": "circle", "lineWidth": 2, "lineColor": PAGE_BG},
        "states": {"hover": {"enabled": False}},
    },
    "line": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"enabled": False}}},
}

scatter_series = ScatterSeries()
scatter_series.data = [[float(c), float(s)] for c, s in zip(cycles, stress, strict=True)]
scatter_series.name = "Test Data"
scatter_series.color = BRAND

fit_series = LineSeries()
fit_series.data = [[float(c), float(s)] for c, s in zip(fit_cycles, fit_stress, strict=True)]
fit_series.name = "Basquin Fit"
fit_series.color = FIT_COLOR

chart.add_series(scatter_series)
chart.add_series(fit_series)

chart.options.credits = {"enabled": False}

# Download Highcharts JS (inline for headless Chrome file:// loading)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
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
# CDP override makes the viewport authoritative; --window-size alone is eaten by Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# PIL safety net: pin to exact 3200×1800 in case of ±1-2 px rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
