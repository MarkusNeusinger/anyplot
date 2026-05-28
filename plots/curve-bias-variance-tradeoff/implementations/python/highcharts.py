"""anyplot.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-28
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.spline import SplineSeries
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

# anyplot palette — first series always #009E73
ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — theoretical bias-variance tradeoff curves
complexity = np.linspace(0.5, 10, 100)
bias_squared = 2.0 / (1 + 0.5 * complexity)
variance = 0.1 * complexity**1.5
irreducible_error = np.full_like(complexity, 0.3)
total_error = bias_squared + variance + irreducible_error

optimal_idx = int(np.argmin(total_error))
optimal_complexity = float(complexity[optimal_idx])
optimal_error = float(total_error[optimal_idx])

# Chart
title = "curve-bias-variance-tradeoff · python · highcharts · anyplot.ai"

chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "spline",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "plotBorderWidth": 0,
    "marginBottom": 180,
    "marginLeft": 220,
    "marginRight": 500,
    "marginTop": 200,
}

chart.options.title = {"text": title, "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK}}

chart.options.subtitle = {
    "text": "Total Error = Bias² + Variance + Irreducible Error",
    "style": {"fontSize": "44px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "title": {"text": "Model Complexity", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "min": 0,
    "max": 10.5,
    "tickInterval": 1,
    "plotBands": [
        {
            "from": 0,
            "to": optimal_complexity,
            "color": "rgba(0,158,115,0.10)",
            "label": {
                "text": "Underfitting Zone",
                "style": {"fontSize": "48px", "color": ANYPLOT_PALETTE[0], "fontWeight": "bold"},
                "verticalAlign": "bottom",
                "align": "center",
                "y": -55,
            },
        },
        {
            "from": optimal_complexity,
            "to": 11,
            "color": "rgba(196,117,253,0.10)",
            "label": {
                "text": "Overfitting Zone",
                "style": {"fontSize": "48px", "color": ANYPLOT_PALETTE[1], "fontWeight": "bold"},
                "verticalAlign": "bottom",
                "align": "center",
                "y": -55,
            },
        },
    ],
    "plotLines": [
        {
            "value": optimal_complexity,
            "color": INK_SOFT,
            "width": 3,
            "dashStyle": "Dash",
            "label": {
                "text": "Optimal",
                "style": {"fontSize": "40px", "color": INK_SOFT},
                "rotation": 0,
                "y": 24,
                "x": 8,
            },
            "zIndex": 5,
        }
    ],
}

chart.options.y_axis = {
    "title": {"text": "Prediction Error", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "min": 0,
    "max": 4.0,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "44px", "fontWeight": "normal", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolWidth": 44,
    "symbolHeight": 16,
    "itemMarginBottom": 12,
    "padding": 20,
}

chart.options.plot_options = {
    "spline": {"lineWidth": 5, "marker": {"enabled": False}},
    "scatter": {"marker": {"radius": 16, "symbol": "circle"}},
}

chart.options.tooltip = {
    "headerFormat": "<b>Complexity: {point.x:.1f}</b><br/>",
    "pointFormat": "{series.name}: <b>{point.y:.3f}</b>",
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "style": {"color": INK, "fontSize": "36px"},
}


# Curve label style helper
def _label_style(color):
    return {"fontSize": "40px", "color": color, "fontWeight": "bold", "textOutline": "none"}


# Series — anyplot palette positions 1-4 in order
# Bias² — last point carries the direct curve annotation
bias_data = [[float(x), float(y)] for x, y in zip(complexity, bias_squared, strict=True)]
bias_data[-1] = {
    "x": float(complexity[-1]),
    "y": float(bias_squared[-1]),
    "dataLabels": {
        "enabled": True,
        "format": "Bias²",
        "align": "left",
        "x": 12,
        "y": -5,
        "crop": False,
        "overflow": "none",
        "style": _label_style(ANYPLOT_PALETTE[0]),
    },
}
bias_series = SplineSeries()
bias_series.name = "Bias²"
bias_series.data = bias_data
bias_series.color = ANYPLOT_PALETTE[0]
chart.add_series(bias_series)

# Variance
variance_data = [[float(x), float(y)] for x, y in zip(complexity, variance, strict=True)]
variance_data[-1] = {
    "x": float(complexity[-1]),
    "y": float(variance[-1]),
    "dataLabels": {
        "enabled": True,
        "format": "Variance",
        "align": "left",
        "x": 12,
        "crop": False,
        "overflow": "none",
        "style": _label_style(ANYPLOT_PALETTE[1]),
    },
}
variance_series = SplineSeries()
variance_series.name = "Variance"
variance_series.data = variance_data
variance_series.color = ANYPLOT_PALETTE[1]
chart.add_series(variance_series)

# Irreducible Error — shift label down to avoid overlap with Bias²
irr_data = [[float(x), float(y)] for x, y in zip(complexity, irreducible_error, strict=True)]
irr_data[-1] = {
    "x": float(complexity[-1]),
    "y": float(irreducible_error[-1]),
    "dataLabels": {
        "enabled": True,
        "format": "Irreducible Error",
        "align": "left",
        "x": 12,
        "y": 30,
        "crop": False,
        "overflow": "none",
        "style": _label_style(ANYPLOT_PALETTE[2]),
    },
}
irreducible_series = SplineSeries()
irreducible_series.name = "Irreducible Error"
irreducible_series.data = irr_data
irreducible_series.color = ANYPLOT_PALETTE[2]
irreducible_series.dash_style = "Dot"
chart.add_series(irreducible_series)

# Total Error — label placed near x≈8 where the curve is well within the y range
_total_label_idx = int(round((8.0 - 0.5) / (10.0 - 0.5) * 99))
total_data = [[float(x), float(y)] for x, y in zip(complexity, total_error, strict=True)]
total_data[_total_label_idx] = {
    "x": float(complexity[_total_label_idx]),
    "y": float(total_error[_total_label_idx]),
    "dataLabels": {
        "enabled": True,
        "format": "Total Error",
        "align": "left",
        "x": 12,
        "y": -10,
        "crop": False,
        "overflow": "none",
        "style": _label_style(ANYPLOT_PALETTE[3]),
    },
}
total_series = SplineSeries()
total_series.name = "Total Error"
total_series.data = total_data
total_series.color = ANYPLOT_PALETTE[3]
total_series.line_width = 8
chart.add_series(total_series)

optimal_series = ScatterSeries()
optimal_series.name = "Optimal Point"
optimal_series.data = [[optimal_complexity, optimal_error]]
optimal_series.color = ANYPLOT_PALETTE[3]
optimal_series.marker = {"radius": 18, "symbol": "diamond", "lineWidth": 3, "lineColor": PAGE_BG}
chart.add_series(optimal_series)

# Download Highcharts JS (required for headless Chrome — CDN blocked on file://)
_req = urllib.request.Request(
    "https://code.highcharts.com/highcharts.js",
    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"},
)
with urllib.request.urlopen(_req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# HTML with inline scripts — all 4 canvas dimensions kept in sync
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

# Screenshot via headless Chrome
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
# CDP override is authoritative — --window-size alone is eaten by Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 3200×1800 — guards against ±1-2 px rounding from CDP
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
