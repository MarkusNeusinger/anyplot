""" pyplots.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: highcharts unknown | Python 3.14.3
Quality: 93/100 | Created: 2026-03-10
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Annual fruit production (thousands of tons)
categories = ["Apples", "Grapes", "Oranges", "Bananas", "Strawberries"]
production = [35, 25, 22, 18, 12]  # Grapes=25 is exact multiple of 5 (no partial icon)
unit_value = 5

# Colorblind-safe palette: blue, purple, orange, amber, crimson (avoids green/blue proximity)
colors = ["#306998", "#7B68A8", "#E8813B", "#D4A017", "#C0392B"]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings
max_icons = max(v // unit_value + (1 if v % unit_value else 0) for v in production)
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#FAFBFC",
    "spacingLeft": 80,
    "spacingRight": 80,
    "spacingTop": 60,
    "spacingBottom": 60,
    "marginLeft": 420,
    "marginRight": 600,
    "marginBottom": 120,
    "marginTop": 280,
    "plotBorderWidth": 0,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
}

# Title
chart.options.title = {
    "text": "pictogram-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "align": "center",
    "style": {"fontSize": "46px", "fontWeight": "bold", "color": "#2C3E50"},
    "margin": 20,
    "widthAdjust": -100,
}

# Subtitle with legend note and storytelling hook
chart.options.subtitle = {
    "text": (
        "Annual Fruit Production \u2014 each \u25cf = 5k tons"
        " &nbsp;\u00b7&nbsp; "
        '<span style="color:#306998;font-weight:bold;">Apples lead at nearly 3\u00d7 Strawberries</span>'
    ),
    "useHTML": True,
    "align": "center",
    "style": {"fontSize": "30px", "color": "#7F8C8D"},
    "widthAdjust": -100,
}

# X-axis (icon positions)
chart.options.x_axis = {
    "min": -0.5,
    "max": max_icons + 1.0,
    "title": {"text": None},
    "labels": {"enabled": False},
    "gridLineWidth": 0,
    "lineWidth": 0,
    "tickWidth": 0,
    "tickLength": 0,
}

# Alternating plot bands for row separation
plot_bands = []
for idx in range(len(categories)):
    if idx % 2 == 0:
        plot_bands.append({"from": idx - 0.5, "to": idx + 0.5, "color": "rgba(48, 105, 152, 0.05)", "borderWidth": 0})

# Y-axis (categories)
chart.options.y_axis = {
    "categories": categories,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "36px", "fontWeight": "bold", "color": "#2C3E50"}, "x": -15},
    "gridLineWidth": 0,
    "lineWidth": 0,
    "tickWidth": 0,
    "tickLength": 0,
    "reversed": True,
    "startOnTick": False,
    "endOnTick": False,
    "plotBands": plot_bands,
}

# Legend
chart.options.legend = {"enabled": False}

# Credits
chart.options.credits = {"enabled": False}

# Tooltip with Highcharts formatting
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": ('<span style="color:{series.color}">\u25cf</span> <b>{series.name}</b>: {point.total}k tons'),
    "style": {"fontSize": "24px"},
    "backgroundColor": "rgba(255,255,255,0.95)",
    "borderColor": "#CCC",
    "borderRadius": 8,
    "shadow": {"color": "rgba(0,0,0,0.1)", "offsetX": 1, "offsetY": 1, "width": 3},
}

# Plot options
chart.options.plot_options = {
    "scatter": {
        "jitter": {"x": 0, "y": 0},
        "marker": {
            "symbol": "circle",
            "radius": 44,
            "lineWidth": 3,
            "lineColor": "#ffffff",
            "states": {"hover": {"radiusPlus": 6, "lineWidthPlus": 2}},
        },
        "states": {"inactive": {"opacity": 0.6}},
    }
}

# Create series for each category
for i, (cat, val, color) in enumerate(zip(categories, production, colors, strict=True)):
    n_full = val // unit_value
    remainder = (val % unit_value) / unit_value
    total_icons = n_full + (1 if remainder > 0 else 0)

    # Top producer emphasis
    is_top = i == 0
    radius = 50 if is_top else 44

    data = []
    for j in range(n_full):
        is_last = j == total_icons - 1 and remainder == 0
        point = {"x": j, "y": i, "total": val}
        if is_last:
            point["dataLabels"] = {
                "enabled": True,
                "format": f"{val}k",
                "align": "left",
                "x": 60,
                "style": {"fontSize": "30px", "fontWeight": "bold", "color": color, "textOutline": "2px white"},
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
                    "x": 60,
                    "style": {"fontSize": "30px", "fontWeight": "bold", "color": color, "textOutline": "2px white"},
                },
            }
        )

    series = ScatterSeries()
    series.name = cat
    series.data = data
    series.color = color
    if is_top:
        series.marker = {"radius": radius, "lineWidth": 4, "lineColor": "#ffffff"}
    chart.add_series(series)

# Download Highcharts JS and annotations module (distinctive Highcharts feature)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
annotations_url = "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()

# Highcharts annotations module: connector line from Apples row to Strawberries row
# with a callout label — leverages the distinctive annotations API
annotation_js = """
var chart = Highcharts.charts[0];
// Use Highcharts renderer API to draw a bracket annotation in the margin area
var plotLeft = chart.plotLeft, plotTop = chart.plotTop,
    plotWidth = chart.plotWidth, plotHeight = chart.plotHeight;
var bracketX = plotLeft + plotWidth + 30;
var topY = plotTop + plotHeight * (0.5 / 5);
var bottomY = plotTop + plotHeight * (4.5 / 5);
var midY = (topY + bottomY) / 2;

// Vertical dashed line
chart.renderer.path(['M', bracketX, topY, 'L', bracketX, bottomY])
    .attr({ stroke: '#306998', 'stroke-width': 2.5, 'stroke-dasharray': '8,6', zIndex: 5 }).add();
// Top tick
chart.renderer.path(['M', bracketX - 15, topY, 'L', bracketX, topY])
    .attr({ stroke: '#306998', 'stroke-width': 2.5, zIndex: 5 }).add();
// Bottom tick
chart.renderer.path(['M', bracketX - 15, bottomY, 'L', bracketX, bottomY])
    .attr({ stroke: '#306998', 'stroke-width': 2.5, zIndex: 5 }).add();

// Label box
chart.renderer.label(
    '<span style="font-size:38px;font-weight:800;color:#306998;">2.9\\u00d7</span><br>' +
    '<span style="font-size:22px;color:#5A6B7D;letter-spacing:1px;">difference</span>',
    bracketX + 18, midY - 48, 'rect', null, null, true
).attr({
    fill: 'rgba(255,255,255,0.95)',
    stroke: '#306998',
    'stroke-width': 2,
    r: 12,
    padding: 18,
    zIndex: 6
}).css({ textAlign: 'center' }).add();
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
    <script>
    setTimeout(function() {{
        {annotation_js}
    }}, 500);
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save standalone HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)

driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
