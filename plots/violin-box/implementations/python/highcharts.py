""" pyplots.ai
violin-box: Violin Plot with Embedded Box Plot
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
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


# Data - generate sample distributions for 4 groups with different characteristics
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C"]
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF"]

# Generate data with different distributions to showcase violin+box features
raw_data = {
    "Control": np.random.normal(50, 10, 150),  # Normal distribution
    "Treatment A": np.concatenate([np.random.normal(45, 6, 80), np.random.normal(70, 6, 70)]),  # Bimodal
    "Treatment B": np.random.normal(65, 8, 150),  # Higher mean, tighter spread
    "Treatment C": np.concatenate([np.random.exponential(10, 120) + 35, [95, 98, 100]]),  # Skewed with outliers
}

# Calculate KDE and box plot statistics for each category
violin_width = 0.35  # Half-width of violin in category units
violin_box_data = []

for i, cat in enumerate(categories):
    data = raw_data[cat]

    # Compute KDE using scipy
    y_min, y_max = data.min() - 5, data.max() + 5
    y_grid = np.linspace(y_min, y_max, 100)
    kde_func = gaussian_kde(data)
    density = kde_func(y_grid)

    # Normalize density to fit within violin width
    density_norm = density / density.max() * violin_width

    # Box plot statistics
    q1 = float(np.percentile(data, 25))
    median = float(np.percentile(data, 50))
    q3 = float(np.percentile(data, 75))
    iqr = q3 - q1
    whisker_low = max(float(data.min()), q1 - 1.5 * iqr)
    whisker_high = min(float(data.max()), q3 + 1.5 * iqr)

    # Identify outliers
    outliers = data[(data < whisker_low) | (data > whisker_high)]

    violin_box_data.append(
        {
            "category": cat,
            "index": i,
            "y_grid": y_grid,
            "density": density_norm,
            "q1": q1,
            "median": median,
            "q3": q3,
            "whisker_low": whisker_low,
            "whisker_high": whisker_high,
            "outliers": [float(o) for o in outliers],
            "color": colors[i],
        }
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
    "marginBottom": 200,
    "marginLeft": 280,
    "marginRight": 120,
}

# Title
chart.options.title = {
    "text": "violin-box \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "84px", "fontWeight": "bold"},
}

# X-axis (categories)
chart.options.x_axis = {
    "title": {"text": "Group", "style": {"fontSize": "56px"}},
    "labels": {"style": {"fontSize": "44px"}, "format": "{value}"},
    "min": -0.5,
    "max": 3.5,
    "tickPositions": [0, 1, 2, 3],
    "categories": categories,
    "lineWidth": 2,
}

# Y-axis (values)
chart.options.y_axis = {
    "title": {"text": "Response Value (units)", "style": {"fontSize": "56px"}},
    "labels": {"style": {"fontSize": "44px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.15)",
}

# Legend
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "44px"}}

# Plot options
chart.options.plot_options = {
    "polygon": {"lineWidth": 3, "fillOpacity": 0.5, "enableMouseTracking": True},
    "scatter": {"marker": {"radius": 16, "symbol": "circle"}, "zIndex": 10},
}

# Add violin shapes as polygon series
for v in violin_box_data:
    # Create polygon points for the violin shape
    polygon_points = []

    # Right side (positive x offset from center)
    for y_val, dens in zip(v["y_grid"], v["density"], strict=True):
        polygon_points.append([float(v["index"] + dens), float(y_val)])

    # Left side (negative x offset from center) - reversed to close the polygon
    for j in range(len(v["y_grid"]) - 1, -1, -1):
        y_val = v["y_grid"][j]
        dens = v["density"][j]
        polygon_points.append([float(v["index"] - dens), float(y_val)])

    series = PolygonSeries()
    series.data = polygon_points
    series.name = v["category"]
    series.color = v["color"]
    series.fill_color = v["color"]
    series.fill_opacity = 0.5
    chart.add_series(series)

# Add embedded box plots inside the violins
box_width = 0.08  # Width of the internal box
whisker_width = 0.04  # Width of the whisker caps

for v in violin_box_data:
    idx = v["index"]

    # Draw the IQR box (Q1 to Q3)
    box_points = [
        [float(idx - box_width), float(v["q1"])],
        [float(idx + box_width), float(v["q1"])],
        [float(idx + box_width), float(v["q3"])],
        [float(idx - box_width), float(v["q3"])],
    ]

    box_series = PolygonSeries()
    box_series.data = box_points
    box_series.name = f"{v['category']} Box"
    box_series.show_in_legend = False
    box_series.color = "#1a1a1a"
    box_series.fill_color = "#ffffff"
    box_series.fill_opacity = 0.9
    box_series.line_width = 4
    chart.add_series(box_series)

    # Draw whisker lines (vertical stem from whisker_low to Q1 and Q3 to whisker_high)
    # Lower whisker line
    lower_whisker_line = PolygonSeries()
    lower_whisker_line.data = [
        [float(idx - 0.01), float(v["whisker_low"])],
        [float(idx + 0.01), float(v["whisker_low"])],
        [float(idx + 0.01), float(v["q1"])],
        [float(idx - 0.01), float(v["q1"])],
    ]
    lower_whisker_line.name = f"{v['category']} Lower Whisker"
    lower_whisker_line.show_in_legend = False
    lower_whisker_line.color = "#1a1a1a"
    lower_whisker_line.fill_color = "#1a1a1a"
    lower_whisker_line.fill_opacity = 1.0
    chart.add_series(lower_whisker_line)

    # Upper whisker line
    upper_whisker_line = PolygonSeries()
    upper_whisker_line.data = [
        [float(idx - 0.01), float(v["q3"])],
        [float(idx + 0.01), float(v["q3"])],
        [float(idx + 0.01), float(v["whisker_high"])],
        [float(idx - 0.01), float(v["whisker_high"])],
    ]
    upper_whisker_line.name = f"{v['category']} Upper Whisker"
    upper_whisker_line.show_in_legend = False
    upper_whisker_line.color = "#1a1a1a"
    upper_whisker_line.fill_color = "#1a1a1a"
    upper_whisker_line.fill_opacity = 1.0
    chart.add_series(upper_whisker_line)

    # Lower whisker cap (horizontal line)
    lower_cap = PolygonSeries()
    lower_cap.data = [
        [float(idx - whisker_width), float(v["whisker_low"] - 0.3)],
        [float(idx + whisker_width), float(v["whisker_low"] - 0.3)],
        [float(idx + whisker_width), float(v["whisker_low"] + 0.3)],
        [float(idx - whisker_width), float(v["whisker_low"] + 0.3)],
    ]
    lower_cap.name = f"{v['category']} Lower Cap"
    lower_cap.show_in_legend = False
    lower_cap.color = "#1a1a1a"
    lower_cap.fill_color = "#1a1a1a"
    lower_cap.fill_opacity = 1.0
    chart.add_series(lower_cap)

    # Upper whisker cap (horizontal line)
    upper_cap = PolygonSeries()
    upper_cap.data = [
        [float(idx - whisker_width), float(v["whisker_high"] - 0.3)],
        [float(idx + whisker_width), float(v["whisker_high"] - 0.3)],
        [float(idx + whisker_width), float(v["whisker_high"] + 0.3)],
        [float(idx - whisker_width), float(v["whisker_high"] + 0.3)],
    ]
    upper_cap.name = f"{v['category']} Upper Cap"
    upper_cap.show_in_legend = False
    upper_cap.color = "#1a1a1a"
    upper_cap.fill_color = "#1a1a1a"
    upper_cap.fill_opacity = 1.0
    chart.add_series(upper_cap)

# Add median markers as scatter points (white fill with dark border for visibility)
med_series = ScatterSeries()
med_series.data = [[float(v["index"]), float(v["median"])] for v in violin_box_data]
med_series.name = "Median"
med_series.color = "#ffffff"
med_series.marker = {"fillColor": "#ffffff", "lineColor": "#1a1a1a", "lineWidth": 5, "radius": 18, "symbol": "circle"}
med_series.z_index = 20
chart.add_series(med_series)

# Add outliers as scatter points
outlier_points = []
for v in violin_box_data:
    for outlier_val in v["outliers"]:
        outlier_points.append([float(v["index"]), outlier_val])

if outlier_points:
    outlier_series = ScatterSeries()
    outlier_series.data = outlier_points
    outlier_series.name = "Outliers"
    outlier_series.color = "#E74C3C"
    outlier_series.marker = {
        "fillColor": "#E74C3C",
        "lineColor": "#C0392B",
        "lineWidth": 3,
        "radius": 14,
        "symbol": "diamond",
    }
    outlier_series.z_index = 15
    chart.add_series(outlier_series)

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
time.sleep(5)  # Wait for chart to render

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
