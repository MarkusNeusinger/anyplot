""" pyplots.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
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
from scipy.spatial import Voronoi
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Generate seed points for Voronoi diagram
np.random.seed(42)
n_points = 20
x_coords = np.random.uniform(15, 85, n_points)
y_coords = np.random.uniform(15, 85, n_points)
labels = [f"Site {i + 1}" for i in range(n_points)]

# Compute Voronoi diagram with added boundary points for proper clipping
points = np.column_stack([x_coords, y_coords])

# Add boundary points to ensure finite regions for interior points
# These help create proper bounded regions
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


# Colorblind-safe colors for Voronoi cells
colors = [
    "#306998",
    "#FFD43B",
    "#9467BD",
    "#17BECF",
    "#8C564B",
    "#1F77B4",
    "#FF7F0E",
    "#2CA02C",
    "#D62728",
    "#E377C2",
    "#7F7F7F",
    "#BCBD22",
    "#4E79A7",
    "#F28E2B",
    "#E15759",
    "#76B7B2",
    "#59A14F",
    "#EDC948",
    "#B07AA1",
    "#FF9DA7",
]

# Build series data for Highcharts
polygon_series = []
scatter_data = []

# Only process the original points (not boundary points)
for idx in range(n_points):
    region_idx = vor.point_region[idx]
    region = vor.regions[region_idx]

    if not region or -1 in region:
        # Skip regions with infinite vertices
        scatter_data.append(
            {"x": float(x_coords[idx]), "y": float(y_coords[idx]), "name": labels[idx], "color": "#1a1a1a"}
        )
        continue

    vertices = vor.vertices
    polygon_points = [[float(vertices[i][0]), float(vertices[i][1])] for i in region]

    # Clip polygon to bounding box
    clipped = clip_polygon_to_bbox(polygon_points, x_min, y_min, x_max, y_max)

    if not clipped or len(clipped) < 3:
        scatter_data.append(
            {"x": float(x_coords[idx]), "y": float(y_coords[idx]), "name": labels[idx], "color": "#1a1a1a"}
        )
        continue

    # Close the polygon
    clipped.append(clipped[0])

    color = colors[idx % len(colors)]

    polygon_series.append(
        {
            "type": "polygon",
            "name": labels[idx],
            "data": clipped,
            "color": color,
            "fillOpacity": 0.5,
            "lineWidth": 3,
            "lineColor": "#333333",
            "enableMouseTracking": True,
            "showInLegend": False,
        }
    )

    # Add seed point
    scatter_data.append({"x": float(x_coords[idx]), "y": float(y_coords[idx]), "name": labels[idx], "color": "#1a1a1a"})

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 220,
    "marginRight": 100,
    "marginTop": 150,
    "spacingBottom": 80,
}

# Title
chart.options.title = {
    "text": "voronoi-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {
    "text": "Spatial partitioning based on proximity to seed points",
    "style": {"fontSize": "28px"},
}

# X-Axis
chart.options.x_axis = {
    "title": {"text": "X Coordinate", "style": {"fontSize": "36px"}, "margin": 30},
    "labels": {"style": {"fontSize": "26px"}},
    "min": 0,
    "max": 100,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "tickInterval": 10,
}

# Y-Axis
chart.options.y_axis = {
    "title": {"text": "Y Coordinate", "style": {"fontSize": "36px"}, "margin": 30},
    "labels": {"style": {"fontSize": "26px"}},
    "min": 0,
    "max": 100,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "tickInterval": 10,
}

# Legend
chart.options.legend = {"enabled": False}

# Credits
chart.options.credits = {"enabled": False}

# Plot options
chart.options.plot_options = {
    "polygon": {"fillOpacity": 0.4, "lineWidth": 3, "states": {"hover": {"fillOpacity": 0.6}}},
    "scatter": {"marker": {"radius": 12, "symbol": "circle", "lineWidth": 2, "lineColor": "#ffffff"}},
}

# Build series list
all_series = polygon_series.copy()

# Add scatter series for seed points
all_series.append(
    {
        "type": "scatter",
        "name": "Seed Points",
        "data": scatter_data,
        "marker": {"radius": 22, "fillColor": "#1a1a1a", "lineWidth": 5, "lineColor": "#ffffff", "symbol": "circle"},
        "zIndex": 10,
        "showInLegend": False,
        "dataLabels": {"enabled": False},
    }
)

# Set series via dictionary approach
chart.options.series = all_series

# Export to PNG via Selenium
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save as plot.html for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
