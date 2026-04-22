""" pyplots.ai
swarm-basic: Basic Swarm Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
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


# Data - employee performance scores by department
np.random.seed(42)
categories = ["Engineering", "Marketing", "Sales", "Operations"]
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF"]

# Generate realistic performance data (different distributions per department)
raw_data = {
    "Engineering": np.concatenate(
        [
            np.random.normal(75, 8, 30),  # Main cluster
            np.random.normal(90, 3, 10),  # High performers
        ]
    ),
    "Marketing": np.random.normal(72, 12, 35),  # Wider spread
    "Sales": np.concatenate(
        [
            np.random.normal(68, 10, 25),  # Lower performers
            np.random.normal(85, 5, 20),  # Top performers (bimodal)
        ]
    ),
    "Operations": np.random.normal(70, 7, 40),  # Tight cluster
}

# Clip values to realistic range (0-100)
for cat in categories:
    raw_data[cat] = np.clip(raw_data[cat], 40, 100)


def compute_swarm_positions(values, bin_width=2.0, point_radius=0.08):
    """
    Compute horizontal jitter for swarm plot using bin-based algorithm.
    Points at similar y-values are spread horizontally to avoid overlap.
    """
    sorted_indices = np.argsort(values)
    sorted_values = values[sorted_indices]

    # Track occupied positions in each bin
    x_positions = np.zeros(len(values))

    for i, (idx, val) in enumerate(zip(sorted_indices, sorted_values, strict=True)):
        # Find nearby points that might overlap
        nearby_mask = np.abs(sorted_values[:i] - val) < bin_width
        nearby_x = x_positions[sorted_indices[:i]][nearby_mask]

        # Find first non-overlapping x position
        x = 0.0
        if len(nearby_x) > 0:
            # Alternate sides and expand outward
            for offset in np.arange(0, 0.5, point_radius * 2):
                for sign in [1, -1]:
                    test_x = sign * offset
                    if offset == 0 and sign == -1:
                        continue
                    if not any(abs(test_x - nx) < point_radius * 2 for nx in nearby_x):
                        x = test_x
                        break
                else:
                    continue
                break
            else:
                # Fallback: place at edge
                x = max(abs(nx) for nx in nearby_x) + point_radius * 2
                x = x if np.random.random() > 0.5 else -x

        x_positions[idx] = x

    return x_positions


# Compute swarm positions for each category
swarm_data = []
for cat_idx, cat in enumerate(categories):
    values = raw_data[cat]
    x_offsets = compute_swarm_positions(values, bin_width=2.5, point_radius=0.06)

    # Create data points: [x, y] where x is category index + jitter
    for val, x_off in zip(values, x_offsets, strict=True):
        swarm_data.append({"x": cat_idx + x_off, "y": float(val), "category": cat, "color": colors[cat_idx]})

# Calculate mean for each category (for median markers)
means = {cat: float(np.mean(raw_data[cat])) for cat in categories}

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
}

# Title
chart.options.title = {
    "text": "swarm-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle describing data
chart.options.subtitle = {"text": "Employee Performance Scores by Department", "style": {"fontSize": "48px"}}

# X-axis (categorical)
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Department", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "tickWidth": 0,
    "lineWidth": 2,
    "min": -0.5,
    "max": len(categories) - 0.5,
    "tickPositions": [0, 1, 2, 3],
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Performance Score", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "gridLineDashStyle": "Dash",
    "min": 35,
    "max": 105,
}

# Legend
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "36px"}}

# Credits
chart.options.credits = {"enabled": False}

# Tooltip
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>{point.category}</b><br/>Score: {point.y:.1f}",
    "style": {"fontSize": "24px"},
}

# Add scatter series for each category (for legend)
for cat_idx, cat in enumerate(categories):
    series = ScatterSeries()
    series.name = cat
    series.color = colors[cat_idx]
    series.data = [{"x": float(pt["x"]), "y": pt["y"], "category": cat} for pt in swarm_data if pt["category"] == cat]
    series.marker = {
        "radius": 14,
        "symbol": "circle",
        "fillColor": colors[cat_idx],
        "lineWidth": 2,
        "lineColor": "#ffffff",
    }
    chart.add_series(series)

# Add mean markers
mean_series = ScatterSeries()
mean_series.name = "Mean"
mean_series.data = [{"x": float(i), "y": means[cat]} for i, cat in enumerate(categories)]
mean_series.marker = {"radius": 20, "symbol": "diamond", "fillColor": "#E74C3C", "lineWidth": 3, "lineColor": "#ffffff"}
mean_series.color = "#E74C3C"
chart.add_series(mean_series)

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
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

# Take screenshot of just the chart container element
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
