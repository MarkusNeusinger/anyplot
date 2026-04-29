""" anyplot.ai
quiver-basic: Basic Quiver Plot
Library: highcharts unknown | Python 3.13.13
Quality: 83/100 | Updated: 2026-04-29
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.18)" if THEME == "light" else "rgba(240,239,232,0.18)"

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
norm_mag = magnitude / max_mag

# Arrow scaling for visual clarity
arrow_scale = 0.18

# Magnitude bins and colors (colorblind-safe sequential: cyan → green → yellow → orange)
num_bins = 4
bin_labels = ["Low", "Medium", "High", "Very High"]
bin_colors = ["#17BECF", "#2AA02A", "#FFD43B", "#FF7F0E"]

# Collect arrow endpoints by magnitude bin
arrow_data = {i: {"shafts": [], "heads": []} for i in range(num_bins)}

head_length_ratio = 0.35
head_angle = 0.5  # radians

for i in range(len(x_flat)):
    if magnitude[i] < 0.15:
        continue

    x1, y1 = float(x_flat[i]), float(y_flat[i])
    u_scaled = U[i] * arrow_scale
    v_scaled = V[i] * arrow_scale
    x2, y2 = x1 + u_scaled, y1 + v_scaled

    arrow_len = np.sqrt(u_scaled**2 + v_scaled**2)
    head_len = arrow_len * head_length_ratio
    angle = np.arctan2(v_scaled, u_scaled)

    x_left = x2 - head_len * np.cos(angle - head_angle)
    y_left = y2 - head_len * np.sin(angle - head_angle)
    x_right = x2 - head_len * np.cos(angle + head_angle)
    y_right = y2 - head_len * np.sin(angle + head_angle)

    bin_idx = min(int(norm_mag[i] * num_bins), num_bins - 1)

    arrow_data[bin_idx]["shafts"].append([[x1, y1], [x2, y2]])
    arrow_data[bin_idx]["heads"].append([[x_left, y_left], [x2, y2], [x_right, y_right]])

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 300,
    "marginLeft": 180,
    "marginRight": 200,
    "marginTop": 150,
}

chart.options.title = {
    "text": "Circular Wind Flow · quiver-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold", "color": INK},
}

chart.options.x_axis = {
    "title": {"text": "X Position (grid units)", "style": {"fontSize": "48px", "color": INK}},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "min": -4,
    "max": 4,
    "tickInterval": 1,
}
chart.options.y_axis = {
    "title": {"text": "Y Position (grid units)", "style": {"fontSize": "48px", "color": INK}},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "min": -4,
    "max": 4,
    "tickInterval": 1,
}

chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "y": -30,
    "itemStyle": {"fontSize": "40px", "color": INK_SOFT},
    "title": {"text": "Vector Magnitude", "style": {"fontSize": "44px", "fontWeight": "bold", "color": INK}},
    "symbolWidth": 80,
    "symbolHeight": 30,
    "itemDistance": 60,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

chart.options.credits = {"enabled": False}

series_list = []

for bin_idx in range(num_bins):
    if not arrow_data[bin_idx]["shafts"]:
        continue

    color = bin_colors[bin_idx]
    label = bin_labels[bin_idx]

    line_data = []
    for shaft in arrow_data[bin_idx]["shafts"]:
        line_data.append({"x": shaft[0][0], "y": shaft[0][1]})
        line_data.append({"x": shaft[1][0], "y": shaft[1][1]})
        line_data.append(None)

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

chart.options.series = series_list

# Download Highcharts JS (required for headless Chrome with file:// protocol)
highcharts_url = "https://unpkg.com/highcharts/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact (inline JS for both themes)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG artifact
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

container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
