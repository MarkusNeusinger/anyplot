""" pyplots.ai
quiver-basic: Basic Quiver Plot
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - create a 12x12 grid with circular rotation pattern (u = -y, v = x)
np.random.seed(42)
grid_size = 12
x_range = np.linspace(-3, 3, grid_size)
y_range = np.linspace(-3, 3, grid_size)
X, Y = np.meshgrid(x_range, y_range)
x_flat = X.flatten()
y_flat = Y.flatten()

# Circular rotation field: u = -y, v = x (counterclockwise rotation)
U = -y_flat
V = x_flat

# Calculate magnitude for color encoding
magnitude = np.sqrt(U**2 + V**2)
max_mag = magnitude.max()

# Normalize magnitude to 0-1 range
norm_mag = magnitude / max_mag

# Arrow scaling for visual clarity
arrow_scale = 0.18


# Color gradient for magnitude (cyan to yellow to orange to red - colorblind-friendly)
def magnitude_to_color(norm_val):
    """Map normalized magnitude (0-1) to colorblind-safe gradient."""
    if norm_val < 0.25:
        # Cyan to teal
        return "#17BECF"
    elif norm_val < 0.5:
        # Teal to yellow-green
        return "#2AA02A"
    elif norm_val < 0.75:
        # Yellow-green to orange
        return "#FFD43B"
    else:
        # Orange to red-orange
        return "#FF7F0E"


# Build arrow data as separate series by magnitude bins for legend
num_bins = 4
bin_labels = ["Low", "Medium", "High", "Very High"]
bin_colors = ["#17BECF", "#2AA02A", "#FFD43B", "#FF7F0E"]

# Collect arrow endpoints by magnitude bin
arrow_data = {i: {"shafts": [], "heads": []} for i in range(num_bins)}

# Arrowhead parameters
head_length_ratio = 0.35
head_angle = 0.5  # radians

for i in range(len(x_flat)):
    # Skip very weak vectors (near center)
    if magnitude[i] < 0.15:
        continue

    # Arrow base and tip
    x1, y1 = float(x_flat[i]), float(y_flat[i])
    u_scaled = U[i] * arrow_scale
    v_scaled = V[i] * arrow_scale
    x2, y2 = x1 + u_scaled, y1 + v_scaled

    # Calculate arrowhead
    arrow_len = np.sqrt(u_scaled**2 + v_scaled**2)
    head_len = arrow_len * head_length_ratio
    angle = np.arctan2(v_scaled, u_scaled)

    # Arrowhead left and right points
    x_left = x2 - head_len * np.cos(angle - head_angle)
    y_left = y2 - head_len * np.sin(angle - head_angle)
    x_right = x2 - head_len * np.cos(angle + head_angle)
    y_right = y2 - head_len * np.sin(angle + head_angle)

    # Determine bin index
    bin_idx = min(int(norm_mag[i] * num_bins), num_bins - 1)

    # Store shaft and arrowhead data
    arrow_data[bin_idx]["shafts"].append([[x1, y1], [x2, y2]])
    arrow_data[bin_idx]["heads"].append([[x_left, y_left], [x2, y2], [x_right, y_right]])


# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 300,
    "marginLeft": 180,
    "marginRight": 200,
    "marginTop": 150,
}

# Title
chart.options.title = {
    "text": "Circular Wind Flow · quiver-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Axes
chart.options.x_axis = {
    "title": {"text": "X Position (grid units)", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.15)",
    "gridLineDashStyle": "Dash",
    "min": -4,
    "max": 4,
    "tickInterval": 1,
}
chart.options.y_axis = {
    "title": {"text": "Y Position (grid units)", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.15)",
    "gridLineDashStyle": "Dash",
    "min": -4,
    "max": 4,
    "tickInterval": 1,
}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "y": -30,
    "itemStyle": {"fontSize": "40px"},
    "title": {"text": "Vector Magnitude", "style": {"fontSize": "44px", "fontWeight": "bold"}},
    "symbolWidth": 80,
    "symbolHeight": 30,
    "itemDistance": 60,
}

# Credits
chart.options.credits = {"enabled": False}

# Add arrow series for each magnitude bin using line type
# We'll use the 'line' series type with lineWidth to draw arrows
series_list = []

for bin_idx in range(num_bins):
    if not arrow_data[bin_idx]["shafts"]:
        continue

    color = bin_colors[bin_idx]
    label = bin_labels[bin_idx]

    # Create line data for this bin - each arrow is a separate segment
    # Using scatter with lineWidth connection won't work, so we build path data
    # Highcharts line series: each segment needs null separator

    line_data = []
    for shaft in arrow_data[bin_idx]["shafts"]:
        line_data.append({"x": shaft[0][0], "y": shaft[0][1]})
        line_data.append({"x": shaft[1][0], "y": shaft[1][1]})
        line_data.append(None)  # Separator for line breaks

    for head in arrow_data[bin_idx]["heads"]:
        line_data.append({"x": head[0][0], "y": head[0][1]})
        line_data.append({"x": head[1][0], "y": head[1][1]})
        line_data.append(None)
        line_data.append({"x": head[1][0], "y": head[1][1]})
        line_data.append({"x": head[2][0], "y": head[2][1]})
        line_data.append(None)

    series_list.append(
        {
            "type": "line",
            "name": label,
            "data": line_data,
            "color": color,
            "lineWidth": 8,
            "marker": {"enabled": False},
            "enableMouseTracking": False,
        }
    )

# Add series via options.series since we're using custom line series
chart.options.series = series_list

# Download Highcharts JS
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

# Save HTML for interactive version
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
