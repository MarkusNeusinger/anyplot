""" anyplot.ai
density-basic: Basic Density Plot
Library: highcharts unknown | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-30
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
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # #009E73
BRAND_RGB = "0, 158, 115"  # BRAND as RGB components for rgba()

# Data — bimodal height distribution (female / male heights in cm)
np.random.seed(42)
n_samples = 500
values_a = np.random.normal(162, 6, n_samples // 2)  # Female heights
values_b = np.random.normal(178, 6, n_samples // 2)  # Male heights
values = np.concatenate([values_a, values_b])

# Kernel Density Estimation with Silverman bandwidth
x_min, x_max = values.min() - 12, values.max() + 12
x_grid = np.linspace(x_min, x_max, 300)
n = len(values)
bandwidth = 0.9 * min(np.std(values), np.subtract(*np.percentile(values, [75, 25])) / 1.34) * n ** (-1 / 5)
density = np.zeros_like(x_grid)
for xi in values:
    density += np.exp(-0.5 * ((x_grid - xi) / bandwidth) ** 2)
density /= n * bandwidth * np.sqrt(2 * np.pi)

# Locate the two bimodal peaks for annotations
midpoint = len(x_grid) // 2
peak1_idx = np.argmax(density[:midpoint])
peak2_idx = midpoint + np.argmax(density[midpoint:])
peak1_x = float(x_grid[peak1_idx])
peak2_x = float(x_grid[peak2_idx])

# Title with auto font-size scaling
title = "density-basic · python · highcharts · anyplot.ai"
n_chars = len(title)
ratio = 67 / n_chars if n_chars > 67 else 1.0
title_fontsize = f"{round(66 * ratio)}px"

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "area",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 160,
    "marginLeft": 180,
    "marginRight": 80,
    "marginTop": 120,
    "style": {"fontFamily": "Arial, Helvetica, sans-serif", "color": INK},
}

chart.options.title = {
    "text": title,
    "style": {"fontSize": title_fontsize, "fontWeight": "600", "color": INK},
    "margin": 40,
}

chart.options.credits = {"enabled": False}

chart.options.colors = IMPRINT_PALETTE

chart.options.x_axis = {
    "title": {"text": "Height (cm)", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickWidth": 0,
    "tickInterval": 5,
    "gridLineWidth": 0,
    "plotBands": [
        {"from": peak1_x - 8, "to": peak1_x + 8, "color": f"rgba({BRAND_RGB}, 0.06)", "zIndex": 0},
        {"from": peak2_x - 8, "to": peak2_x + 8, "color": f"rgba({BRAND_RGB}, 0.06)", "zIndex": 0},
    ],
    "plotLines": [
        {
            "value": peak1_x,
            "color": f"rgba({BRAND_RGB}, 0.50)",
            "width": 3,
            "dashStyle": "Dash",
            "zIndex": 4,
            "label": {
                "text": f"Peak: {peak1_x:.0f} cm",
                "style": {"fontSize": "34px", "color": INK_SOFT, "fontWeight": "600"},
                "rotation": 0,
                "y": 16,
            },
        },
        {
            "value": peak2_x,
            "color": f"rgba({BRAND_RGB}, 0.50)",
            "width": 3,
            "dashStyle": "Dash",
            "zIndex": 4,
            "label": {
                "text": f"Peak: {peak2_x:.0f} cm",
                "style": {"fontSize": "34px", "color": INK_SOFT, "fontWeight": "600"},
                "rotation": 0,
                "y": 16,
            },
        },
    ],
}

chart.options.y_axis = {
    "title": {"text": "Density", "style": {"fontSize": "56px", "color": INK}, "margin": 24},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickAmount": 7,
    "min": 0,
}

chart.options.plot_options = {
    "area": {
        "fillColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [[0, f"rgba({BRAND_RGB}, 0.45)"], [1, f"rgba({BRAND_RGB}, 0.03)"]],
        },
        "lineWidth": 5,
        "marker": {"enabled": False},
        "color": BRAND,
        "states": {"hover": {"lineWidth": 5}},
    },
    "scatter": {
        "marker": {"radius": 4, "fillColor": f"rgba({BRAND_RGB}, 0.30)", "symbol": "circle", "lineWidth": 0},
        "states": {"hover": {"enabled": False}},
    },
    "series": {"animation": False},
}

chart.options.tooltip = {"enabled": False}

chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "right",
    "verticalAlign": "top",
    "floating": True,
    "x": -40,
    "y": 60,
    "itemStyle": {"fontSize": "44px", "fontWeight": "normal", "color": INK_SOFT},
    "symbolHeight": 20,
    "symbolWidth": 32,
    "itemDistance": 40,
    "borderWidth": 0,
    "backgroundColor": "rgba(0,0,0,0)",
}

# Density curve as area series
area_series = AreaSeries()
area_series.data = [[round(float(x), 2), round(float(y), 6)] for x, y in zip(x_grid, density, strict=True)]
area_series.name = "Density"
chart.add_series(area_series)

# Rug plot — every 3rd observation as small circles (radius 4, 30% opacity avoids overlap clutter)
rug_sample = values[::3]
rug_y = max(density) * 0.008
rug_data = [[round(float(v), 2), round(float(rug_y), 6)] for v in sorted(rug_sample)]

rug_series = ScatterSeries()
rug_series.data = rug_data
rug_series.name = "Observations"
rug_series.marker = {"symbol": "circle", "fillColor": f"rgba({BRAND_RGB}, 0.30)", "lineWidth": 0, "radius": 4}
chart.add_series(rug_series)

# Download Highcharts JS for inline embedding (required for headless Chrome)
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

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML for screenshot
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
# CDP override is authoritative — --window-size alone leaves Chrome chrome eating ~139 px
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dims (safety net for ±1-2 px rounding)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
