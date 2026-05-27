""" anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-17
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from scipy.spatial import Voronoi
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette - first color is always brand green
IMPRINT = [
    "#009E73",  # bluish green (brand)
    "#C475FD",  # vermillion
    "#4467A3",  # blue
    "#BD8233",  # reddish purple
    "#AE3030",  # orange
    "#2ABCCD",  # sky blue
    "#954477",  # yellow
]

# Data - Generate seed points for Voronoi diagram
np.random.seed(42)
n_points = 20
x_coords = np.random.uniform(15, 85, n_points)
y_coords = np.random.uniform(15, 85, n_points)
labels = [f"Site {i + 1}" for i in range(n_points)]

# Compute Voronoi diagram with added boundary points for proper clipping
points = np.column_stack([x_coords, y_coords])

# Add boundary points to ensure finite regions for interior points
boundary_margin = 200
boundary_points = np.array(
    [
        [-boundary_margin, -boundary_margin],
        [-boundary_margin, 100 + boundary_margin],
        [100 + boundary_margin, -boundary_margin],
        [100 + boundary_margin, 100 + boundary_margin],
        [50, -boundary_margin],
        [50, 100 + boundary_margin],
        [-boundary_margin, 50],
        [100 + boundary_margin, 50],
    ]
)
all_points = np.vstack([points, boundary_points])
vor = Voronoi(all_points)

# Bounding box for clipping
x_min, x_max = 0, 100
y_min, y_max = 0, 100


def clip_polygon_to_bbox(polygon, x_min, y_min, x_max, y_max):
    """Clip a polygon to a rectangular bounding box using Sutherland-Hodgman algorithm."""

    def inside_edge(p, edge):
        x, y = p
        if edge == "left":
            return x >= x_min
        elif edge == "right":
            return x <= x_max
        elif edge == "bottom":
            return y >= y_min
        elif edge == "top":
            return y <= y_max

    def compute_intersection(p1, p2, edge):
        x1, y1 = p1
        x2, y2 = p2
        if edge == "left":
            t = (x_min - x1) / (x2 - x1) if x2 != x1 else 0
            return [x_min, y1 + t * (y2 - y1)]
        elif edge == "right":
            t = (x_max - x1) / (x2 - x1) if x2 != x1 else 0
            return [x_max, y1 + t * (y2 - y1)]
        elif edge == "bottom":
            t = (y_min - y1) / (y2 - y1) if y2 != y1 else 0
            return [x1 + t * (x2 - x1), y_min]
        elif edge == "top":
            t = (y_max - y1) / (y2 - y1) if y2 != y1 else 0
            return [x1 + t * (x2 - x1), y_max]

    output = polygon
    for edge in ["left", "right", "bottom", "top"]:
        if not output:
            return []
        input_list = output
        output = []
        for i in range(len(input_list)):
            current = input_list[i]
            previous = input_list[i - 1]
            if inside_edge(current, edge):
                if not inside_edge(previous, edge):
                    output.append(compute_intersection(previous, current, edge))
                output.append(current)
            elif inside_edge(previous, edge):
                output.append(compute_intersection(previous, current, edge))
    return output


# Build series data for Highcharts
polygon_series = []
scatter_data = []

# Only process the original points (not boundary points)
for idx in range(n_points):
    region_idx = vor.point_region[idx]
    region = vor.regions[region_idx]

    if not region or -1 in region:
        scatter_data.append({"x": float(x_coords[idx]), "y": float(y_coords[idx]), "name": labels[idx], "color": INK})
        continue

    vertices = vor.vertices
    polygon_points = [[float(vertices[i][0]), float(vertices[i][1])] for i in region]

    # Clip polygon to bounding box
    clipped = clip_polygon_to_bbox(polygon_points, x_min, y_min, x_max, y_max)

    if not clipped or len(clipped) < 3:
        scatter_data.append({"x": float(x_coords[idx]), "y": float(y_coords[idx]), "name": labels[idx], "color": INK})
        continue

    # Close the polygon
    clipped.append(clipped[0])

    color = IMPRINT[idx % len(IMPRINT)]

    polygon_series.append(
        {
            "type": "polygon",
            "name": labels[idx],
            "data": clipped,
            "color": color,
            "fillOpacity": 0.5,
            "lineWidth": 3,
            "lineColor": INK_SOFT,
            "enableMouseTracking": True,
            "showInLegend": False,
        }
    )

    # Add seed point
    scatter_data.append({"x": float(x_coords[idx]), "y": float(y_coords[idx]), "name": labels[idx], "color": INK})

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 250,
    "marginLeft": 220,
    "marginRight": 100,
    "marginTop": 150,
    "spacingBottom": 80,
}

# Title
chart.options.title = {
    "text": "voronoi-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# Subtitle
chart.options.subtitle = {
    "text": "Spatial partitioning based on proximity to seed points",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-Axis
chart.options.x_axis = {
    "title": {"text": "X Coordinate", "style": {"fontSize": "22px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 0,
    "max": 100,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "tickInterval": 10,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Y-Axis
chart.options.y_axis = {
    "title": {"text": "Y Coordinate", "style": {"fontSize": "22px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 0,
    "max": 100,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "tickInterval": 10,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Legend
chart.options.legend = {"enabled": False}

# Credits
chart.options.credits = {"enabled": False}

# Plot options
chart.options.plot_options = {
    "polygon": {"fillOpacity": 0.4, "lineWidth": 3, "states": {"hover": {"fillOpacity": 0.6}}},
    "scatter": {"marker": {"radius": 12, "symbol": "circle", "lineWidth": 2, "lineColor": PAGE_BG}},
}

# Build series list
all_series = polygon_series.copy()

# Add scatter series for seed points
all_series.append(
    {
        "type": "scatter",
        "name": "Seed Points",
        "data": scatter_data,
        "marker": {"radius": 22, "fillColor": INK, "lineWidth": 5, "lineColor": PAGE_BG, "symbol": "circle"},
        "zIndex": 10,
        "showInLegend": False,
        "dataLabels": {"enabled": False},
    }
)

# Set series via dictionary approach
chart.options.series = all_series


# Export to PNG via Selenium - fetch Highcharts JS with retry
def fetch_url(url, max_retries=3):
    """Fetch URL with retry logic."""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://anyplot.ai/",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError:
            if attempt == max_retries - 1:
                raise
            time.sleep(2**attempt)  # Exponential backoff
    return None


highcharts_js = fetch_url("https://code.highcharts.com/highcharts.js")
highcharts_more_js = fetch_url("https://code.highcharts.com/highcharts-more.js")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
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
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
