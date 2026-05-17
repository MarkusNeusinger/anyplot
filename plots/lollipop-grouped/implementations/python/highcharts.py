""" anyplot.ai
lollipop-grouped: Grouped Lollipop Chart
Library: highcharts unknown | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-17
"""

import os
import ssl
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series ALWAYS #009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2"]

# Data - Quarterly revenue by product line across regions
np.random.seed(42)
categories = ["North", "South", "East", "West"]
series_names = ["Electronics", "Furniture", "Clothing"]

# Generate revenue data (in millions)
data = {"Electronics": [4.2, 3.8, 5.1, 4.5], "Furniture": [2.8, 3.2, 2.5, 3.0], "Clothing": [3.5, 4.1, 3.3, 3.8]}

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "marginLeft": 250,
    "marginRight": 350,
}

# Title
chart.options.title = {
    "text": "lollipop-grouped · Python · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "normal"},
    "margin": 40,
}

# X-axis (categories)
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Region", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "tickWidth": 0,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Revenue ($ Millions)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 0,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolRadius": 8,
    "symbolHeight": 16,
    "symbolWidth": 16,
    "itemMarginBottom": 20,
}

# Plot options
chart.options.plot_options = {"scatter": {"marker": {"radius": 8, "lineWidth": 0}}}

# Build series data with lollipop stems using scatter points
all_series = []

# Calculate offsets for grouped lollipops
n_series = len(series_names)
offsets = [(i - (n_series - 1) / 2) * 0.2 for i in range(n_series)]

for series_name, color, offset in zip(series_names, OKABE_ITO, offsets, strict=True):
    values = data[series_name]
    # Create scatter points for the markers
    scatter_data = []
    for cat_idx, val in enumerate(values):
        scatter_data.append({"x": cat_idx + offset, "y": val})

    series = ScatterSeries()
    series.name = series_name
    series.data = scatter_data
    series.color = color
    series.marker = {"radius": 8, "symbol": "circle"}
    all_series.append(series)

for s in all_series:
    chart.add_series(s)

# Generate JavaScript with custom stem rendering
js_literal = chart.to_js_literal()

# Custom JavaScript to draw stems
stem_drawing_js = """
Highcharts.addEvent(Highcharts.Chart, 'render', function() {
    var chart = this;

    // Remove old stems
    if (chart.customStems) {
        chart.customStems.forEach(function(stem) {
            stem.destroy();
        });
    }
    chart.customStems = [];

    chart.series.forEach(function(series) {
        series.points.forEach(function(point) {
            var x = point.plotX + chart.plotLeft;
            var y = point.plotY + chart.plotTop;
            var baseline = chart.plotTop + chart.plotHeight;

            var stem = chart.renderer.path([
                'M', x, baseline,
                'L', x, y
            ])
            .attr({
                'stroke-width': 2,
                stroke: series.color,
                zIndex: 1
            })
            .add();

            chart.customStems.push(stem);
        });
    });
});
"""

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
ssl_context = ssl._create_unverified_context()
request = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://anyplot.ai"})
with urllib.request.urlopen(request, timeout=30, context=ssl_context) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    {stem_drawing_js}
    {js_literal}
    </script>
</body>
</html>"""

# Write HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot for PNG
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
