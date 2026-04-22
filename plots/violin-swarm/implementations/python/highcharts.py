""" pyplots.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
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


# Data - Reaction times (ms) across 4 experimental conditions
np.random.seed(42)
categories = ["Control", "Condition A", "Condition B", "Condition C"]
# Violin fills with transparency, darker point colors for contrast
colors_violin = [
    "rgba(48, 105, 152, 0.4)",
    "rgba(255, 212, 59, 0.4)",
    "rgba(148, 103, 189, 0.4)",
    "rgba(23, 190, 207, 0.4)",
]
colors_points = ["#1a3d5c", "#c9a200", "#5c3d7a", "#0d7a85"]  # Darker variants for points
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
            "color_violin": colors_violin[i],
            "color_points": colors_points[i],
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
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
    "marginLeft": 280,
    "marginRight": 150,
}

# Title
chart.options.title = {
    "text": "violin-swarm · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {
    "text": "Reaction Times Across Experimental Conditions",
    "style": {"fontSize": "42px", "color": "#666666"},
}

# X-axis (categories)
chart.options.x_axis = {
    "title": {"text": "Experimental Condition", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "38px"}},
    "min": -0.6,
    "max": 3.6,
    "tickPositions": [0, 1, 2, 3],
    "categories": categories,
    "lineWidth": 2,
    "lineColor": "#333333",
}

# Y-axis (values)
chart.options.y_axis = {
    "title": {"text": "Reaction Time (ms)", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "38px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.12)",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "38px"},
    "symbolHeight": 24,
    "symbolWidth": 24,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "y": 30,
}

# Plot options
chart.options.plot_options = {
    "polygon": {"lineWidth": 2, "fillOpacity": 0.35, "enableMouseTracking": False},
    "scatter": {"marker": {"radius": 10, "symbol": "circle", "lineWidth": 2}, "zIndex": 10},
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
    series.color = v["color_points"]  # Border color
    series.fill_color = v["color_violin"]  # Semi-transparent fill
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
    scatter_series.color = v["color_points"]
    scatter_series.marker = {
        "fillColor": v["color_points"],
        "lineColor": "#ffffff",
        "lineWidth": 2,
        "radius": 12,  # Larger markers for visibility
        "symbol": "circle",
    }
    scatter_series.z_index = 10
    chart.add_series(scatter_series)

# Download Highcharts JS files
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Polygon requires highcharts-more.js
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
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
