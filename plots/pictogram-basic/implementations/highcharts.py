"""pyplots.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: highcharts unknown | Python 3.14.3
Quality: 78/100 | Created: 2026-03-10
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
production = [35, 28, 22, 18, 12]
unit_value = 5

colors = ["#306998", "#7B68A8", "#E8813B", "#2ECC71", "#E74C3C"]

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
    "marginRight": 350,
    "marginBottom": 120,
    "marginTop": 250,
    "plotBorderWidth": 0,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
}

# Title - explicitly centered with enough spacing
chart.options.title = {
    "text": "pictogram-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "align": "center",
    "style": {"fontSize": "46px", "fontWeight": "bold", "color": "#2C3E50"},
    "margin": 30,
    "widthAdjust": -100,
}

# Subtitle with legend note
chart.options.subtitle = {
    "text": f"Annual Fruit Production \u2014 each \u25cf = {unit_value}k tons",
    "align": "center",
    "style": {"fontSize": "32px", "color": "#7F8C8D"},
    "widthAdjust": -100,
}

# X-axis (icon positions) - generous max to prevent clipping
chart.options.x_axis = {
    "min": -0.5,
    "max": max_icons + 0.5,
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
        plot_bands.append({"from": idx - 0.5, "to": idx + 0.5, "color": "rgba(48, 105, 152, 0.04)", "borderWidth": 0})

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
    "pointFormat": '<span style="color:{series.color}">\u25cf</span> <b>{series.name}</b>: {point.total}k tons',
    "style": {"fontSize": "24px"},
    "backgroundColor": "rgba(255,255,255,0.95)",
    "borderColor": "#CCC",
    "borderRadius": 8,
    "shadow": {"color": "rgba(0,0,0,0.1)", "offsetX": 1, "offsetY": 1, "width": 3},
}

# Plot options with data labels for value annotations
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

# Create series for each category with data labels on last point
for i, (cat, val, color) in enumerate(zip(categories, production, colors, strict=True)):
    n_full = val // unit_value
    remainder = (val % unit_value) / unit_value
    total_icons = n_full + (1 if remainder > 0 else 0)

    data = []
    for j in range(n_full):
        is_last = j == total_icons - 1 and remainder == 0
        point = {"x": j, "y": i, "total": val}
        if is_last:
            point["dataLabels"] = {
                "enabled": True,
                "format": f"{val}k",
                "align": "left",
                "x": 55,
                "style": {"fontSize": "28px", "fontWeight": "bold", "color": color, "textOutline": "2px white"},
            }
        data.append(point)

    if remainder > 0:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
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
                    "x": 55,
                    "style": {"fontSize": "28px", "fontWeight": "bold", "color": color, "textOutline": "2px white"},
                },
            }
        )

    # Highlight top producer with larger markers
    series = ScatterSeries()
    series.name = cat
    series.data = data
    series.color = color
    if i == 0:
        series.marker = {"radius": 48, "lineWidth": 4, "lineColor": "#ffffff"}
    chart.add_series(series)

# Download Highcharts JS
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
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
time.sleep(5)

driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
