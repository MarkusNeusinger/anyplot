""" anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: highcharts unknown | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-15
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.spline import SplineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

iris = load_iris()
X = StandardScaler().fit_transform(iris.data)
y = iris.target
species_names = ["Setosa", "Versicolor", "Virginica"]

t = np.linspace(-np.pi, np.pi, 200)


def andrews_curve(x, t):
    n = len(x)
    result = x[0] / np.sqrt(2)
    for i in range(1, n):
        if i % 2 == 1:
            result += x[i] * np.sin((i // 2 + 1) * t)
        else:
            result += x[i] * np.cos((i // 2) * t)
    return result


chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 180,
    "marginTop": 120,
    "marginLeft": 150,
    "marginRight": 100,
}

chart.options.title = {
    "text": "andrews-curves · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK},
    "y": 30,
}

chart.options.x_axis = {
    "title": {"text": "t (radians)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "tickInterval": 1,
    "min": -3.15,
    "max": 3.15,
}

chart.options.y_axis = {
    "title": {"text": "f(t)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "tickInterval": 1,
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "symbolWidth": 30,
    "symbolHeight": 2,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 50,
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "padding": 15,
}

chart.options.plot_options = {
    "line": {"lineWidth": 3, "marker": {"enabled": False}, "animation": False},
    "series": {"animation": False},
}

np.random.seed(42)
samples_per_species = 20

for species_idx in range(3):
    species_mask = y == species_idx
    species_X = X[species_mask]
    sample_indices = np.random.choice(len(species_X), min(samples_per_species, len(species_X)), replace=False)

    for i, idx in enumerate(sample_indices):
        curve_values = andrews_curve(species_X[idx], t)
        data_points = [[float(t[j]), float(curve_values[j])] for j in range(len(t))]

        series = SplineSeries()
        series.data = data_points
        series.name = species_names[species_idx]
        series.color = IMPRINT[species_idx]
        series.opacity = 0.5
        series.show_in_legend = i == 0
        series.line_width = 2

        chart.add_series(series)

highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
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
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
