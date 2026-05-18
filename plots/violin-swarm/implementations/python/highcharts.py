"""pyplots.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: highcharts | Python 3.13.11
Quality: 91/100 | Updated: 2026-05-18
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.polygon import PolygonSeries
from highcharts_core.options.series.scatter import ScatterSeries
from scipy.stats import gaussian_kde
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme configuration
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette - first series is always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Reaction times (ms) across 4 experimental conditions
np.random.seed(42)
categories = ["Control", "Condition A", "Condition B", "Condition C"]
n_obs = 50

# Generate distinct distributions for each condition
raw_data = {
    "Control": np.random.normal(350, 45, n_obs),  # Normal distribution
    "Condition A": np.random.normal(280, 35, n_obs),  # Faster responses, lower variance
    "Condition B": np.concatenate(
        [np.random.normal(320, 25, n_obs // 2), np.random.normal(420, 30, n_obs // 2)]
    ),  # Bimodal
    "Condition C": np.random.exponential(50, n_obs) + 270,  # Right-skewed
}

# Calculate KDE for violin shapes
violin_width = 0.35
violin_data = []

for i, cat in enumerate(categories):
    data = raw_data[cat]

    # Compute KDE
    y_min, y_max = data.min() - 20, data.max() + 20
    y_grid = np.linspace(y_min, y_max, 100)
    kde_func = gaussian_kde(data)
    density = kde_func(y_grid)

    # Normalize density to fit within violin width
    density_norm = density / density.max() * violin_width

    violin_data.append(
        {
            "category": cat,
            "index": i,
            "y_grid": y_grid,
            "density": density_norm,
            "raw_data": data,
            "color": OKABE_ITO[i],
        }
    )


# Swarm layout function - position points to avoid overlap within violin bounds
def swarm_positions(data, index, density_norm, y_grid):
    """Calculate x positions for swarm points within violin bounds."""
    sorted_indices = np.argsort(data)
    sorted_data = data[sorted_indices]

    # For each point, find position within violin width
    x_positions = np.zeros(len(data))

    for j, y_val in enumerate(sorted_data):
        # Find width of violin at this y value
        y_idx = np.argmin(np.abs(y_grid - y_val))
        max_width = density_norm[y_idx] * 0.9  # Stay slightly inside violin

        # Find available x position that doesn't overlap with nearby points
        placed = False
        for attempt_x in np.linspace(0, max_width, 20):
            conflict = False
            for k in range(j):
                if abs(sorted_data[k] - y_val) < 10:  # Within 10ms vertically
                    if abs(x_positions[k] - attempt_x) < 0.04:  # Too close horizontally
                        conflict = True
                        break
            if not conflict:
                x_positions[j] = attempt_x if j % 2 == 0 else -attempt_x
                placed = True
                break

        if not placed:
            # Random jitter within bounds as fallback
            x_positions[j] = np.random.uniform(-max_width, max_width)

    # Reorder to original order
    result = np.zeros(len(data))
    result[sorted_indices] = x_positions
    return index + result


# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "marginLeft": 280,
    "marginRight": 150,
}

# Title
chart.options.title = {
    "text": "violin-swarm · highcharts · pyplots.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# Subtitle
chart.options.subtitle = {
    "text": "Reaction Times Across Experimental Conditions",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis (categories)
chart.options.x_axis = {
    "title": {"text": "Experimental Condition", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": -0.6,
    "max": 3.6,
    "tickPositions": [0, 1, 2, 3],
    "categories": categories,
    "lineWidth": 2,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Y-axis (values)
chart.options.y_axis = {
    "title": {"text": "Reaction Time (ms)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "symbolHeight": 24,
    "symbolWidth": 24,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "y": 30,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Plot options
chart.options.plot_options = {
    "polygon": {"lineWidth": 2, "fillOpacity": 0.35, "enableMouseTracking": False},
    "scatter": {"marker": {"radius": 8, "symbol": "circle", "lineWidth": 2}, "zIndex": 10},
}

# Add violin shapes as polygon series (background)
for v in violin_data:
    polygon_points = []

    # Right side
    for y_val, dens in zip(v["y_grid"], v["density"], strict=True):
        polygon_points.append([float(v["index"] + dens), float(y_val)])

    # Left side (reversed)
    for j in range(len(v["y_grid"]) - 1, -1, -1):
        y_val = v["y_grid"][j]
        dens = v["density"][j]
        polygon_points.append([float(v["index"] - dens), float(y_val)])

    series = PolygonSeries()
    series.data = polygon_points
    series.name = f"{v['category']} (distribution)"
    series.color = v["color"]
    series.fill_color = v["color"]
    series.fill_opacity = 0.35
    series.show_in_legend = False
    series.z_index = 1
    chart.add_series(series)

# Add swarm points for each category (foreground)
for v in violin_data:
    # Calculate swarm positions
    x_positions = swarm_positions(v["raw_data"], v["index"], v["density"], v["y_grid"])

    # Create scatter series for swarm points
    scatter_series = ScatterSeries()
    scatter_series.data = [[float(x), float(y)] for x, y in zip(x_positions, v["raw_data"], strict=True)]
    scatter_series.name = v["category"]
    scatter_series.color = v["color"]
    scatter_series.marker = {
        "fillColor": v["color"],
        "lineColor": "#ffffff",
        "lineWidth": 2,
        "radius": 8,
        "symbol": "circle",
    }
    scatter_series.z_index = 10
    chart.add_series(scatter_series)

# Download Highcharts JS files with fallback CDNs
cdn_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.min.js",
    "https://unpkg.com/highcharts@11/highcharts.js",
    "https://code.highcharts.com/highcharts.js",
]

highcharts_js = None
for url in cdn_urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
    max_retries = 2
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
                break
        except (urllib.error.URLError, urllib.error.HTTPError):
            if attempt < max_retries - 1:
                time.sleep(1)
    if highcharts_js:
        break

if not highcharts_js:
    raise RuntimeError("Could not download Highcharts from any CDN")

# Polygon requires highcharts-more.js - try multiple CDN sources
cdn_more_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.min.js",
    "https://unpkg.com/highcharts@11/modules/highcharts-more.js",
    "https://code.highcharts.com/highcharts-more.js",
]

highcharts_more_js = None
for url in cdn_more_urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
    max_retries = 2
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_more_js = response.read().decode("utf-8")
                break
        except (urllib.error.URLError, urllib.error.HTTPError):
            if attempt < max_retries - 1:
                time.sleep(1)
    if highcharts_more_js:
        break

if not highcharts_more_js:
    raise RuntimeError("Could not download Highcharts-more from any CDN")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive viewing
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML file for screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Take screenshot with Selenium
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
