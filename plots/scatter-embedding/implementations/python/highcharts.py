""" anyplot.ai
scatter-embedding: t-SNE and UMAP Embedding Visualization
Library: highcharts unknown | Python 3.13.13
Quality: 85/100 | Created: 2026-05-07
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import make_blobs
from sklearn.manifold import TSNE


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data — simulate scRNA-seq cell types, project to 2D via t-SNE
np.random.seed(42)
cell_types = ["T CD4+", "T CD8+", "B cells", "NK cells", "Monocytes", "Dendritic"]
n_clusters = len(cell_types)
n_per_cluster = 200

X, y = make_blobs(
    n_samples=n_per_cluster * n_clusters, n_features=50, centers=n_clusters, cluster_std=2.5, random_state=42
)
X_2d = TSNE(n_components=2, perplexity=30, max_iter=500, random_state=42).fit_transform(X)

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif", "color": INK},
    "spacingTop": 80,
    "spacingRight": 320,
    "spacingBottom": 80,
    "spacingLeft": 80,
}

chart.options.title = {
    "text": "Cell-type Atlas · scatter-embedding · highcharts · anyplot.ai",
    "align": "left",
    "x": 40,
    "style": {"fontSize": "56px", "fontWeight": "600", "color": INK, "letterSpacing": "-0.5px"},
    "margin": 16,
}

chart.options.subtitle = {
    "text": "t-SNE (perplexity=30) — 1 200 single cells across 6 immune cell types",
    "align": "left",
    "x": 40,
    "style": {"fontSize": "28px", "fontWeight": "400", "color": INK_MUTED},
}

chart.options.x_axis = {
    "title": {
        "text": "t-SNE Dimension 1",
        "style": {"fontSize": "36px", "fontWeight": "500", "color": INK},
        "margin": 24,
    },
    "labels": {"enabled": False},
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickLength": 0,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

chart.options.y_axis = {
    "title": {
        "text": "t-SNE Dimension 2",
        "style": {"fontSize": "36px", "fontWeight": "500", "color": INK},
        "margin": 24,
    },
    "labels": {"enabled": False},
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickLength": 0,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"color": INK_SOFT, "fontSize": "28px", "fontWeight": "400"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "borderRadius": 8,
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "middle",
    "symbolRadius": 8,
    "symbolHeight": 20,
    "symbolWidth": 20,
    "padding": 32,
    "itemMarginBottom": 16,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 10,
    "borderWidth": 1,
    "shadow": False,
    "style": {"fontSize": "22px", "color": INK},
    "headerFormat": "<b>{series.name}</b><br>",
    "pointFormat": "({point.x:.2f}, {point.y:.2f})",
}

chart.options.plot_options = {
    "scatter": {
        "marker": {"radius": 12, "symbol": "circle", "lineWidth": 1, "lineColor": PAGE_BG, "fillOpacity": 0.65},
        "states": {"hover": {"halo": {"size": 10, "opacity": 0.15}}},
        "stickyTracking": False,
    }
}

# One series per immune cell type
for i, (label, color) in enumerate(zip(cell_types, IMPRINT, strict=True)):
    series = ScatterSeries()
    series.name = label
    series.color = color
    cluster_pts = X_2d[y == i]
    series.data = [[float(pt[0]), float(pt[1])] for pt in cluster_pts]
    chart.add_series(series)

# Download Highcharts JS (headless Chrome cannot load CDN from file://)
highcharts_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

chart_js = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
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
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
