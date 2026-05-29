""" anyplot.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: highcharts unknown | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-29
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries
from highcharts_core.options.series.spline import SplineSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — canonical order, position 1 always first series
COLOR_GINI = "#009E73"  # Imprint position 1 — brand green
COLOR_ENTROPY = "#C475FD"  # Imprint position 2 — lavender

# Data
p = np.linspace(0, 1, 200)
gini = 2 * p * (1 - p)
with np.errstate(divide="ignore", invalid="ignore"):
    entropy_raw = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
entropy = np.nan_to_num(entropy_raw, nan=0.0)

gini_data = [[round(float(p[i]), 4), round(float(gini[i]), 6)] for i in range(len(p))]
entropy_data = [[round(float(p[i]), 4), round(float(entropy[i]), 6)] for i in range(len(p))]
area_range_data = [
    [round(float(p[i]), 4), round(float(gini[i]), 6), round(float(entropy[i]), 6)] for i in range(len(p))
]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginLeft": 180,
    "marginRight": 160,
    "marginBottom": 200,
    "marginTop": 160,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

# Title: 59 chars — below 67-char baseline, default 66px
chart.options.title = {
    "text": "line-impurity-comparison · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK},
}

# Subtitle explains practical significance (storytelling context)
chart.options.subtitle = {
    "text": "Both criteria peak at p = 0.5, producing near-identical tree splits in practice",
    "style": {"fontSize": "44px", "color": INK_SOFT, "fontWeight": "400"},
}

chart.options.x_axis = {
    "title": {"text": "Probability (p)", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": 0,
    "max": 1,
    "tickInterval": 0.1,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "crosshair": {"width": 2, "color": GRID, "dashStyle": "Dash"},
}

chart.options.y_axis = {
    "title": {"text": "Impurity Measure [0–1]", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": 0,
    "max": 1.1,
    "endOnTick": False,
    "tickInterval": 0.2,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "plotLines": [
        {
            "value": 0.5,
            "color": COLOR_GINI,
            "width": 2,
            "dashStyle": "LongDash",
            "label": {
                "text": "Gini max = 0.5",
                "align": "right",
                "x": -10,
                "style": {"fontSize": "36px", "color": COLOR_GINI, "fontWeight": "600"},
            },
            "zIndex": 3,
        },
        {
            "value": 1.0,
            "color": COLOR_ENTROPY,
            "width": 2,
            "dashStyle": "LongDash",
            "label": {
                "text": "Entropy max = 1.0",
                "align": "left",
                "x": 10,
                "style": {"fontSize": "36px", "color": COLOR_ENTROPY, "fontWeight": "600"},
            },
            "zIndex": 3,
        },
    ],
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 100,
    "itemStyle": {"fontSize": "44px", "fontWeight": "normal", "color": INK_SOFT},
    "itemMarginBottom": 15,
    "backgroundColor": ELEVATED_BG,
    "borderRadius": 10,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "padding": 24,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "shared": True,
    "backgroundColor": ELEVATED_BG,
    "borderRadius": 8,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "style": {"fontSize": "36px", "color": INK},
    "headerFormat": '<span style="font-size: 36px; font-weight: bold;">p = {point.key:.3f}</span><br/>',
    "pointFormat": '<span style="color:{series.color}">●</span> {series.name}: <b>{point.y:.4f}</b><br/>',
}

chart.options.plot_options = {
    "series": {"animation": False},
    "spline": {"lineWidth": 7, "marker": {"enabled": False}},
    "arearange": {"lineWidth": 0, "marker": {"enabled": False}, "enableMouseTracking": False},
}

# Annotation at p=0.5 highlighting both maxima
chart.options.annotations = [
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": ELEVATED_BG,
            "borderColor": INK_SOFT,
            "borderRadius": 8,
            "borderWidth": 2,
            "style": {"fontSize": "36px", "color": INK},
            "padding": 14,
        },
        "labels": [
            {
                "point": {"x": 0.5, "y": 1.0, "xAxis": 0, "yAxis": 0},
                "text": "Both peak at p = 0.5<br/>Entropy = 1.0 │ Gini = 0.5",
                "y": -45,
            }
        ],
    }
]

# Fill between curves — visible at 15% opacity (was effectively ~0.6% due to double-applied alpha)
fill_series = AreaRangeSeries()
fill_series.data = area_range_data
fill_series.name = "Difference"
fill_series.color = COLOR_ENTROPY
fill_series.fill_opacity = 0.15
fill_series.show_in_legend = False
chart.add_series(fill_series)

# Gini series (Imprint position 1 — brand green, always first)
gini_series = SplineSeries()
gini_series.data = gini_data
gini_series.name = "Gini Impurity: 2p(1−p)"
gini_series.color = COLOR_GINI
chart.add_series(gini_series)

# Entropy series (Imprint position 2 — lavender)
entropy_series = SplineSeries()
entropy_series.data = entropy_data
entropy_series.name = "Entropy: −p log₂p − (1−p) log₂(1−p)"
entropy_series.color = COLOR_ENTROPY
chart.add_series(entropy_series)

# Download Highcharts JS libraries (User-Agent required — bare urlopen returns 403)
_headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"}

with urllib.request.urlopen(
    urllib.request.Request("https://code.highcharts.com/highcharts.js", headers=_headers), timeout=30
) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(
    urllib.request.Request("https://code.highcharts.com/highcharts-more.js", headers=_headers), timeout=30
) as response:
    highcharts_more_js = response.read().decode("utf-8")

with urllib.request.urlopen(
    urllib.request.Request("https://code.highcharts.com/modules/annotations.js", headers=_headers), timeout=30
) as response:
    annotations_js = response.read().decode("utf-8")

# Build HTML with inline scripts (CDN unavailable from file:// in headless Chrome)
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome — four canvas settings must all agree: window-size,
# CDP override (authoritative), HTML div, and chart.options.chart width/height
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

# Belt-and-braces: pin to exact 3200×1800 in case of ±1–2 px rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
