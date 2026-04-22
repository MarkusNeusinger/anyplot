""" pyplots.ai
ridgeline-basic: Basic Ridgeline Plot
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Monthly temperature distributions showing seasonal patterns
np.random.seed(42)
months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# Generate realistic temperature distributions for each month (°C)
# Colder in winter, warmer in summer with varying spread
month_params = {
    "January": (2, 4),
    "February": (4, 4),
    "March": (8, 5),
    "April": (12, 5),
    "May": (17, 5),
    "June": (21, 4),
    "July": (24, 3),
    "August": (23, 3),
    "September": (19, 4),
    "October": (14, 5),
    "November": (8, 5),
    "December": (4, 4),
}

raw_data = {}
for month in months:
    mean, std = month_params[month]
    raw_data[month] = np.random.normal(mean, std, 200)


# Kernel Density Estimation (Gaussian kernel)
def kde(data, x_grid, bandwidth=None):
    """Compute Gaussian KDE at given x values."""
    n = len(data)
    if bandwidth is None:
        # Silverman's rule of thumb
        bandwidth = 1.06 * np.std(data) * n ** (-1 / 5)
    result = np.zeros_like(x_grid)
    for xi in data:
        result += np.exp(-0.5 * ((x_grid - xi) / bandwidth) ** 2)
    result /= n * bandwidth * np.sqrt(2 * np.pi)
    return result


# Common x-axis range for all ridges
x_min = -10
x_max = 35
x_grid = np.linspace(x_min, x_max, 200)

# Calculate KDE for each month
ridge_data = []
for i, month in enumerate(months):
    data = raw_data[month]
    density = kde(data, x_grid)
    ridge_data.append({"month": month, "index": i, "density": density})

# Normalize densities for consistent ridge heights
max_density = max(r["density"].max() for r in ridge_data)
ridge_scale = 0.7  # Scale factor for ridge height relative to spacing
ridge_spacing = 1.0  # Vertical spacing between ridges

# Colors - gradient from cool (winter) to warm (summer) and back
colors = [
    "#306998",  # January - cold blue
    "#4A7BA8",  # February
    "#6E9DBF",  # March
    "#8FBF8F",  # April - spring green
    "#A8D08D",  # May
    "#FFD43B",  # June - warm yellow
    "#FFB347",  # July - summer orange
    "#FFD43B",  # August
    "#A8D08D",  # September
    "#8FBF8F",  # October
    "#6E9DBF",  # November
    "#4A7BA8",  # December
]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
    "marginLeft": 300,
    "marginRight": 100,
    "marginTop": 150,
}

# Title
chart.options.title = {
    "text": "Monthly Temperatures · ridgeline-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
}

# X-axis (temperature values)
chart.options.x_axis = {
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "min": x_min,
    "max": x_max,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "tickInterval": 5,
}

# Y-axis (months, stacked vertically)
chart.options.y_axis = {
    "title": {"text": "", "enabled": False},
    "labels": {
        "style": {"fontSize": "32px"},
        "formatter": """function() {
            var months = ['January', 'February', 'March', 'April', 'May', 'June',
                         'July', 'August', 'September', 'October', 'November', 'December'];
            var idx = Math.round(this.value);
            if (idx >= 0 && idx < months.length) {
                return months[idx];
            }
            return '';
        }""",
    },
    "tickPositions": list(range(12)),
    "gridLineWidth": 0,
    "min": -0.5,
    "max": 12.5,
}

# Legend
chart.options.legend = {"enabled": False}

# Plot options for areas
chart.options.plot_options = {
    "area": {"fillOpacity": 0.7, "lineWidth": 3, "marker": {"enabled": False}, "enableMouseTracking": True}
}

# Add ridge series (in reverse order so January is at top)
for i in range(len(months) - 1, -1, -1):
    r = ridge_data[i]
    month = r["month"]
    density = r["density"]

    # Normalize and offset density to create ridge effect
    # Each ridge is centered at its month index
    base_y = i  # Base y position for this month
    scaled_density = (density / max_density) * ridge_scale

    # Create area data: x = temperature, y = base + scaled density
    area_data = []
    for x_val, d_val in zip(x_grid, scaled_density, strict=True):
        area_data.append([float(x_val), float(base_y + d_val)])

    series = AreaSeries()
    series.data = area_data
    series.name = month
    series.color = colors[i]
    series.fill_color = {
        "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
        "stops": [
            [0, colors[i]],
            [1, f"{colors[i]}33"],  # Fade to transparent
        ],
    }
    series.threshold = float(base_y)  # Fill from baseline
    chart.add_series(series)

# Download Highcharts JS for inline embedding
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

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
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
    f.write(standalone_html)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render

# Screenshot the chart element specifically for exact 4800x2700
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
