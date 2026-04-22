""" pyplots.ai
silhouette-basic: Silhouette Plot
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2025-12-26
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import BarSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Simulated silhouette scores for 3-cluster solution
# Mimics Iris dataset clustering with realistic distributions
np.random.seed(42)
n_clusters = 3

# Cluster 0: Well-separated (high silhouette values)
cluster_0 = np.clip(np.random.beta(5, 2, 50) * 0.8 + 0.2, -1, 1)

# Cluster 1: Moderate separation (mix of high and medium values)
cluster_1 = np.clip(np.random.beta(4, 3, 50) * 0.9 + 0.05, -1, 1)

# Cluster 2: Some overlap (wider distribution, includes negative values for misclassified samples)
cluster_2_base = np.random.beta(3, 2, 50) * 1.1 - 0.3  # Shift down to get negatives
cluster_2 = np.clip(cluster_2_base, -1, 1)

all_silhouette_vals = np.concatenate([cluster_0, cluster_1, cluster_2])
avg_silhouette = float(np.mean(all_silhouette_vals))

# Prepare data for silhouette plot - sorted within each cluster
cluster_data = [np.sort(cluster_0), np.sort(cluster_1), np.sort(cluster_2)]

# Colors for clusters (colorblind-safe)
colors = ["#306998", "#FFD43B", "#9467BD"]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "bar",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 180,
    "marginRight": 150,
    "marginBottom": 120,
}

# Title
chart.options.title = {
    "text": "silhouette-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle showing average silhouette score
chart.options.subtitle = {
    "text": f"Iris Dataset Clustering (K=3) | Average Silhouette Score: {avg_silhouette:.3f}",
    "style": {"fontSize": "32px"},
}

# Build categories (sample indices) and series data
# Each sample gets a category, grouped by cluster
categories = []
all_series_data = [[] for _ in range(n_clusters)]

sample_idx = 0
cluster_boundaries = []
cluster_centers = []

for cluster_id in range(n_clusters):
    start_idx = sample_idx
    cluster_silhouette = cluster_data[cluster_id]
    cluster_avg = np.mean(cluster_silhouette)

    for val in cluster_silhouette:
        categories.append("")  # Empty labels to avoid clutter
        for j in range(n_clusters):
            if j == cluster_id:
                all_series_data[j].append(float(val))
            else:
                all_series_data[j].append(None)
        sample_idx += 1

    end_idx = sample_idx - 1
    cluster_boundaries.append(end_idx)
    cluster_centers.append((start_idx + end_idx) / 2)

# X-axis (vertical in bar chart - this is the sample axis)
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Samples (sorted by silhouette score within cluster)", "style": {"fontSize": "28px"}},
    "labels": {"enabled": False},
    "gridLineWidth": 0,
    "plotBands": [
        {
            "from": 0 if i == 0 else cluster_boundaries[i - 1] + 0.5,
            "to": cluster_boundaries[i] + 0.5,
            "color": f"rgba({int(colors[i][1:3], 16)}, {int(colors[i][3:5], 16)}, {int(colors[i][5:7], 16)}, 0.08)",
            "label": {
                "text": f"Cluster {i}<br>Avg: {np.mean(cluster_data[i]):.3f}",
                "style": {"fontSize": "24px", "fontWeight": "bold"},
                "align": "left",
                "x": 10,
                "y": 5,
            },
        }
        for i in range(n_clusters)
    ],
}

# Y-axis (horizontal in bar chart - this is the silhouette score axis)
chart.options.y_axis = {
    "title": {"text": "Silhouette Coefficient", "style": {"fontSize": "28px"}, "margin": 20},
    "labels": {"style": {"fontSize": "22px"}},
    "min": -0.3,
    "max": 1.0,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "plotLines": [
        {
            "value": avg_silhouette,
            "color": "#E74C3C",
            "width": 4,
            "dashStyle": "Dash",
            "label": {
                "text": f"Average: {avg_silhouette:.3f}",
                "style": {"fontSize": "24px", "fontWeight": "bold", "color": "#E74C3C"},
                "align": "left",
                "rotation": 0,
                "y": -10,
                "x": 5,
            },
            "zIndex": 5,
        },
        {"value": 0, "color": "#333333", "width": 2, "zIndex": 4},
    ],
}

# Tooltip for interactive features
chart.options.tooltip = {
    "enabled": True,
    "headerFormat": "",
    "pointFormat": '<span style="color:{point.color}">\u25cf</span> <b>{series.name}</b><br/>Silhouette Score: <b>{point.y:.3f}</b>',
    "style": {"fontSize": "20px"},
}

# Plot options
chart.options.plot_options = {
    "bar": {"stacking": None, "groupPadding": 0, "pointPadding": 0, "borderWidth": 0},
    "series": {
        "animation": False,
        "states": {"hover": {"enabled": True, "brightness": 0.15}, "inactive": {"opacity": 0.5}},
    },
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "24px"},
    "verticalAlign": "top",
    "align": "right",
    "layout": "vertical",
    "x": -50,
    "y": 100,
}

# Add series for each cluster
for cluster_id in range(n_clusters):
    series = BarSeries()
    series.name = f"Cluster {cluster_id} (n={len(cluster_data[cluster_id])})"
    series.data = all_series_data[cluster_id]
    series.color = colors[cluster_id]
    chart.add_series(series)

# Export to PNG via Selenium
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Also save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    cdn_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(cdn_html)

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
