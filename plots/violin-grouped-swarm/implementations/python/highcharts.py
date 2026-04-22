""" pyplots.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
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
from highcharts_core.options.series.polygon import PolygonSeries
from highcharts_core.options.series.scatter import ScatterSeries
from scipy.stats import gaussian_kde
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Response times (ms) across task types and expertise levels
np.random.seed(42)

categories = ["Pattern Match", "Memory Recall", "Calculation"]
groups = ["Novice", "Expert"]
colors = {"Novice": "#306998", "Expert": "#FFD43B"}

# Generate realistic response time data
raw_data = {}
for cat in categories:
    raw_data[cat] = {}
    if cat == "Pattern Match":
        raw_data[cat]["Novice"] = np.random.lognormal(6.2, 0.4, 45)
        raw_data[cat]["Expert"] = np.random.lognormal(5.8, 0.3, 40)
    elif cat == "Memory Recall":
        raw_data[cat]["Novice"] = np.random.lognormal(6.5, 0.5, 50)
        raw_data[cat]["Expert"] = np.random.lognormal(5.9, 0.25, 42)
    else:  # Calculation
        raw_data[cat]["Novice"] = np.random.lognormal(6.8, 0.45, 48)
        raw_data[cat]["Expert"] = np.random.lognormal(6.0, 0.35, 44)


# Swarm algorithm - simple jitter with collision avoidance
def create_swarm_points(y_values, x_center, width, point_size=0.03):
    """Create swarm points with jittered x positions to avoid overlap."""
    sorted_indices = np.argsort(y_values)
    sorted_y = y_values[sorted_indices]

    x_positions = np.zeros(len(y_values))

    for i, idx in enumerate(sorted_indices):
        y_val = sorted_y[i]
        x_pos = x_center

        # Check for collisions with previously placed points
        placed = False
        for offset in np.linspace(0, width / 2, 20):
            for sign in [1, -1]:
                test_x = x_center + sign * offset
                collision = False
                for j in range(i):
                    prev_idx = sorted_indices[j]
                    if abs(sorted_y[j] - y_val) < point_size * 800:  # vertical overlap
                        if abs(x_positions[prev_idx] - test_x) < point_size:  # horizontal overlap
                            collision = True
                            break
                if not collision:
                    x_pos = test_x
                    placed = True
                    break
            if placed:
                break

        x_positions[idx] = x_pos

    return x_positions


# Violin and swarm data preparation
violin_width = 0.25  # Half-width of each violin
group_offset = 0.35  # Offset between groups within category
swarm_width = violin_width * 0.8  # Swarm should fit within violin

violin_data = []
swarm_data = []

for i, cat in enumerate(categories):
    for j, group in enumerate(groups):
        values = raw_data[cat][group]
        offset = -group_offset if j == 0 else group_offset
        x_center = i + offset

        # Compute KDE for violin shape
        y_min, y_max = values.min() - 50, values.max() + 50
        y_grid = np.linspace(y_min, y_max, 100)
        kde_func = gaussian_kde(values)
        density = kde_func(y_grid)
        density_norm = density / density.max() * violin_width

        violin_data.append(
            {
                "category": cat,
                "group": group,
                "x_center": x_center,
                "y_grid": y_grid,
                "density": density_norm,
                "color": colors[group],
            }
        )

        # Create swarm points
        x_positions = create_swarm_points(values, x_center, swarm_width)
        swarm_data.append(
            {"category": cat, "group": group, "x_positions": x_positions, "y_values": values, "color": colors[group]}
        )

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
    "marginLeft": 300,
    "marginRight": 200,
    "marginTop": 150,
}

# Title
chart.options.title = {
    "text": "violin-grouped-swarm · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
    "y": 60,
}

chart.options.subtitle = {
    "text": "Response Times by Task Type and Expertise Level",
    "style": {"fontSize": "40px", "color": "#666666"},
    "y": 120,
}

# X-axis (categories)
chart.options.x_axis = {
    "title": {"text": "Task Type", "style": {"fontSize": "48px"}, "margin": 30},
    "labels": {"style": {"fontSize": "40px"}, "y": 50},
    "min": -0.8,
    "max": 2.8,
    "tickPositions": [0, 1, 2],
    "categories": categories,
    "lineWidth": 2,
}

# Y-axis (values)
chart.options.y_axis = {
    "title": {"text": "Response Time (ms)", "style": {"fontSize": "48px"}, "margin": 40},
    "labels": {"style": {"fontSize": "40px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.12)",
    "min": 0,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -80,
    "y": 150,
    "itemStyle": {"fontSize": "40px", "fontWeight": "normal"},
    "symbolHeight": 24,
    "symbolWidth": 40,
    "itemMarginBottom": 15,
}

# Plot options
chart.options.plot_options = {
    "polygon": {"lineWidth": 2, "fillOpacity": 0.5, "enableMouseTracking": True},
    "scatter": {"marker": {"radius": 8, "symbol": "circle"}, "zIndex": 10},
}

# Track legend entries
legend_added = {"Novice": False, "Expert": False}

# Add violin shapes as polygon series
for v in violin_data:
    polygon_points = []

    # Right side (positive offset from center)
    for y_val, dens in zip(v["y_grid"], v["density"], strict=True):
        polygon_points.append([float(v["x_center"] + dens), float(y_val)])

    # Left side (negative offset from center) - reversed
    for k in range(len(v["y_grid"]) - 1, -1, -1):
        y_val = v["y_grid"][k]
        dens = v["density"][k]
        polygon_points.append([float(v["x_center"] - dens), float(y_val)])

    show_in_legend = not legend_added[v["group"]]
    legend_added[v["group"]] = True

    series = PolygonSeries()
    series.data = polygon_points
    series.name = v["group"]
    series.show_in_legend = show_in_legend
    series.color = v["color"]
    series.fill_color = v["color"]
    series.fill_opacity = 0.5
    chart.add_series(series)

# Add swarm points as scatter series
for s in swarm_data:
    scatter_points = [[float(x), float(y)] for x, y in zip(s["x_positions"], s["y_values"], strict=True)]

    scatter = ScatterSeries()
    scatter.data = scatter_points
    scatter.name = f"{s['group']} data"
    scatter.show_in_legend = False
    scatter.color = s["color"]
    scatter.marker = {"radius": 6, "symbol": "circle", "fillColor": s["color"], "lineColor": "#ffffff", "lineWidth": 1}
    scatter.z_index = 15
    chart.add_series(scatter)

# Download Highcharts JS files
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(standalone_html)

# Take screenshot with Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
