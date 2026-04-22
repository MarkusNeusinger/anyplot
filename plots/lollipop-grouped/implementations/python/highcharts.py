""" pyplots.ai
lollipop-grouped: Grouped Lollipop Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

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


# Data - Quarterly revenue by product line across regions
np.random.seed(42)
categories = ["North", "South", "East", "West"]
series_names = ["Electronics", "Furniture", "Clothing"]
colors = ["#306998", "#FFD43B", "#9467BD"]

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
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
    "marginLeft": 250,
    "marginRight": 350,
}

# Title
chart.options.title = {
    "text": "lollipop-grouped · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
    "margin": 50,
}

# X-axis (categories)
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Region", "style": {"fontSize": "48px"}, "margin": 30},
    "labels": {"style": {"fontSize": "40px"}},
    "lineWidth": 3,
    "tickWidth": 0,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Revenue ($ Millions)", "style": {"fontSize": "48px"}, "margin": 30},
    "labels": {"style": {"fontSize": "36px"}},
    "min": 0,
    "gridLineWidth": 2,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "40px"},
    "symbolRadius": 12,
    "symbolHeight": 24,
    "symbolWidth": 24,
    "itemMarginBottom": 20,
}

# Plot options
chart.options.plot_options = {"scatter": {"marker": {"radius": 28, "lineWidth": 0}}}

# Build series data with lollipop stems using scatter points
all_series = []

# Calculate offsets for grouped lollipops
n_series = len(series_names)
offsets = [(i - (n_series - 1) / 2) * 0.2 for i in range(n_series)]

for series_name, color, offset in zip(series_names, colors, offsets, strict=True):
    values = data[series_name]
    # Create scatter points for the markers
    scatter_data = []
    for cat_idx, val in enumerate(values):
        scatter_data.append({"x": cat_idx + offset, "y": val})

    series = ScatterSeries()
    series.name = series_name
    series.data = scatter_data
    series.color = color
    series.marker = {"radius": 28, "symbol": "circle"}
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
                'stroke-width': 6,
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
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    {stem_drawing_js}
    {js_literal}
    </script>
</body>
</html>"""

# Write temp HTML and save as plot.html
with open("plot.html", "w", encoding="utf-8") as f:
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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
