""" anyplot.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: highcharts unknown | Python 3.13.13
Quality: 93/100 | Updated: 2026-06-03
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
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

# Imprint palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — Annual fruit production (thousands of tons)
categories = ["Apples", "Grapes", "Oranges", "Bananas", "Strawberries"]
production = [35, 25, 22, 18, 12]
unit_value = 5

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

max_icons = max(v // unit_value + (1 if v % unit_value else 0) for v in production)

chart.options.chart = {
    "type": "scatter",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginLeft": 320,
    "marginRight": 280,
    "marginTop": 180,
    "marginBottom": 70,
    "plotBorderWidth": 0,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
}

# Title — scaled by length (67-char baseline = 66px)
title_text = "pictogram-basic · python · highcharts · anyplot.ai"
n = len(title_text)
ratio = 67 / n if n > 67 else 1.0
title_px = max(44, round(66 * ratio))

chart.options.title = {
    "text": title_text,
    "align": "center",
    "style": {"fontSize": f"{title_px}px", "fontWeight": "bold", "color": INK},
    "margin": 16,
}

chart.options.subtitle = {
    "text": (
        "Annual Fruit Production — each ● = 5k tons"
        " &nbsp;·&nbsp; "
        '<span style="color:#009E73;font-weight:bold;">Apples lead at nearly 3× Strawberries</span>'
    ),
    "useHTML": True,
    "align": "center",
    "style": {"fontSize": "36px", "color": INK_SOFT},
}

# X-axis (icon column positions)
chart.options.x_axis = {
    "min": -0.5,
    "max": max_icons + 1.5,
    "title": {"text": None},
    "labels": {"enabled": False},
    "gridLineWidth": 0,
    "lineWidth": 0,
    "tickWidth": 0,
}

# Alternating bands for row separation — theme-adaptive green tint
band_fill = "rgba(0,158,115,0.06)" if THEME == "light" else "rgba(0,158,115,0.09)"
plot_bands = [
    {"from": i - 0.5, "to": i + 0.5, "color": band_fill, "borderWidth": 0} for i in range(len(categories)) if i % 2 == 0
]

# Y-axis (category rows)
chart.options.y_axis = {
    "categories": categories,
    "title": {"text": ""},
    "labels": {"style": {"fontSize": "44px", "fontWeight": "bold", "color": INK}, "x": -12},
    "gridLineWidth": 0,
    "lineWidth": 0,
    "tickWidth": 0,
    "reversed": True,
    "startOnTick": False,
    "endOnTick": False,
    "plotBands": plot_bands,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": ('<span style="color:{series.color}">●</span> <b>{series.name}</b>: {point.total}k tons'),
    "style": {"fontSize": "24px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
}

chart.options.plot_options = {
    "scatter": {
        "marker": {
            "symbol": "circle",
            "radius": 38,
            "lineWidth": 3,
            "lineColor": PAGE_BG,
            "states": {"hover": {"radiusPlus": 5, "lineWidthPlus": 2}},
        },
        "states": {"inactive": {"opacity": 0.6}},
    }
}

# Series — one per fruit category
for i, (cat, val, color) in enumerate(zip(categories, production, IMPRINT_PALETTE, strict=True)):
    n_full = val // unit_value
    remainder = (val % unit_value) / unit_value
    total_icons = n_full + (1 if remainder > 0 else 0)
    is_top = i == 0
    radius = 42 if is_top else 38

    data = []
    for j in range(n_full):
        is_last_full = j == n_full - 1 and remainder == 0
        point = {"x": j, "y": i, "total": val}
        if is_last_full:
            point["dataLabels"] = {
                "enabled": True,
                "format": f"{val}k",
                "align": "left",
                "x": 58,
                "style": {"fontSize": "30px", "fontWeight": "bold", "color": color, "textOutline": f"2px {PAGE_BG}"},
            }
        data.append(point)

    if remainder > 0:
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        data.append(
            {
                "x": n_full,
                "y": i,
                "total": val,
                "marker": {"fillColor": f"rgba({r},{g},{b},{round(remainder, 2)})"},
                "dataLabels": {
                    "enabled": True,
                    "format": f"{val}k",
                    "align": "left",
                    "x": 58,
                    "style": {
                        "fontSize": "30px",
                        "fontWeight": "bold",
                        "color": color,
                        "textOutline": f"2px {PAGE_BG}",
                    },
                },
            }
        )

    series = ScatterSeries()
    series.name = cat
    series.data = data
    series.color = color
    if is_top:
        series.marker = {"radius": radius, "lineWidth": 4, "lineColor": PAGE_BG}
    chart.add_series(series)

# Download Highcharts JS for inline embedding (required in headless Chrome)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()

# Theme-adaptive JS variables for the renderer annotation
annotation_vars = f"var BRACKET_COLOR = '#009E73';var LABEL_COLOR = '{INK_SOFT}';var LABEL_BG = '{ELEVATED_BG}';"

# Highcharts renderer API — bracket comparing Apples row to Strawberries row
annotation_js = """
var chart = Highcharts.charts[0];
var plotLeft = chart.plotLeft, plotTop = chart.plotTop,
    plotWidth = chart.plotWidth, plotHeight = chart.plotHeight;
var bracketX = plotLeft + plotWidth + 30;
var topY = plotTop + plotHeight * (0.5 / 5);
var bottomY = plotTop + plotHeight * (4.5 / 5);
var midY = (topY + bottomY) / 2;

chart.renderer.path(['M', bracketX, topY, 'L', bracketX, bottomY])
    .attr({ stroke: BRACKET_COLOR, 'stroke-width': 2.5, 'stroke-dasharray': '8,6', zIndex: 5 }).add();
chart.renderer.path(['M', bracketX - 15, topY, 'L', bracketX, topY])
    .attr({ stroke: BRACKET_COLOR, 'stroke-width': 2.5, zIndex: 5 }).add();
chart.renderer.path(['M', bracketX - 15, bottomY, 'L', bracketX, bottomY])
    .attr({ stroke: BRACKET_COLOR, 'stroke-width': 2.5, zIndex: 5 }).add();

chart.renderer.label(
    '<span style="font-size:32px;font-weight:800;color:' + BRACKET_COLOR + ';">2.9\\u00d7</span><br>' +
    '<span style="font-size:20px;color:' + LABEL_COLOR + ';letter-spacing:1px;">difference</span>',
    bracketX + 18, midY - 40, 'rect', null, null, true
).attr({
    fill: LABEL_BG,
    stroke: BRACKET_COLOR,
    'stroke-width': 2,
    r: 10,
    padding: 14,
    zIndex: 6
}).css({ textAlign: 'center' }).add();
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
    <script>
    setTimeout(function() {{
        {annotation_vars}
        {annotation_js}
    }}, 500);
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via Selenium with CDP viewport override
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
# CDP override is authoritative — --window-size alone loses ~139 px to Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# PIL safety net — pin to exact 3200×1800 so the post-render gate passes
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
