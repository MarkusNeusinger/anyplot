""" anyplot.ai
horizon-basic: Horizon Chart
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-07
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (from prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data: Server CPU metrics over 24 hours for 6 servers
np.random.seed(42)
n_points = 200
n_series = 6
series_names = ["Server A", "Server B", "Server C", "Server D", "Server E", "Server F"]

# Generate time points over 24 hours
hours = np.linspace(0, 24, n_points)

# Generate realistic CPU usage patterns with variations from baseline
data = []
for i, name in enumerate(series_names):
    # Different patterns for each server
    base = np.sin(hours * np.pi / 12 + i * 0.5) * 15  # Daily cycle
    noise = np.cumsum(np.random.randn(n_points) * 0.5)  # Random walk
    spikes = np.random.choice([0, 1], n_points, p=[0.95, 0.05]) * np.random.randn(n_points) * 20
    values = base + noise + spikes
    data.append({"series": name, "hours": hours.tolist(), "values": values.tolist()})

# Horizon chart parameters
n_bands = 3

# Color scheme: Okabe-Ito green shades for positive, orange shades for negative
# Positive: from light to dark shades of #009E73 (Okabe-Ito position 1)
colors_pos = ["#6FD8C0", "#009E73", "#004A3A"]  # Light to dark green
# Negative: from light to dark shades of #D55E00 (Okabe-Ito position 2)
colors_neg = ["#F4B3A0", "#D55E00", "#6B2F00"]  # Light to dark orange

# Calculate global max for consistent band sizing
all_values = np.concatenate([np.array(d["values"]) for d in data])
band_size = float(np.max(np.abs(all_values)) / n_bands)

# Build custom Highcharts configuration for horizon chart
chart_height = 2700
chart_width = 4800
row_height = (chart_height - 250) / n_series  # Reserve space for title and x-axis

# Build series data for all bands across all servers
series_configs = []
y_axis_configs = []

for row_idx, series_data in enumerate(data):
    values = np.array(series_data["values"])
    x = series_data["hours"]
    name = series_data["series"]

    # Y-axis for this row
    y_axis_configs.append(
        {
            "top": f"{int(row_idx * row_height / chart_height * 100) + 5}%",
            "height": f"{int(row_height / chart_height * 100) - 2}%",
            "offset": 0,
            "labels": {"enabled": True, "style": {"fontSize": "16px", "color": INK_SOFT}, "align": "right", "x": -10},
            "title": {
                "text": name,
                "align": "high",
                "rotation": 0,
                "x": -10,
                "y": 0,
                "style": {"fontSize": "22px", "fontWeight": "bold", "color": INK},
            },
            "min": 0,
            "max": band_size,
            "gridLineWidth": 0,
            "lineColor": INK_SOFT,
            "tickColor": INK_SOFT,
        }
    )

    # Create bands for positive values (folded)
    for band in range(n_bands):
        band_min = band * band_size
        band_max = (band + 1) * band_size

        # Clip positive values to this band
        y_pos = np.clip(values, band_min, band_max) - band_min
        y_pos = np.where(values > band_min, y_pos, 0)

        # Create data points
        series_data_points = [[float(xv), float(yv)] for xv, yv in zip(x, y_pos, strict=False)]

        series_configs.append(
            {
                "type": "area",
                "data": series_data_points,
                "yAxis": row_idx,
                "color": colors_pos[band],
                "fillOpacity": 1,
                "lineWidth": 0,
                "marker": {"enabled": False},
                "showInLegend": False,
                "enableMouseTracking": False,
            }
        )

    # Create bands for negative values (folded, mirrored to positive)
    for band in range(n_bands):
        band_min = band * band_size
        band_max = (band + 1) * band_size

        # Clip negative values (absolute) to this band and mirror
        neg_values = np.abs(np.minimum(values, 0))
        y_neg = np.clip(neg_values, band_min, band_max) - band_min
        y_neg = np.where(neg_values > band_min, y_neg, 0)

        # Create data points
        series_data_points = [[float(xv), float(yv)] for xv, yv in zip(x, y_neg, strict=False)]

        series_configs.append(
            {
                "type": "area",
                "data": series_data_points,
                "yAxis": row_idx,
                "color": colors_neg[band],
                "fillOpacity": 1,
                "lineWidth": 0,
                "marker": {"enabled": False},
                "showInLegend": False,
                "enableMouseTracking": False,
            }
        )

# Build the Highcharts options as JSON string
chart_options = {
    "chart": {
        "type": "area",
        "width": chart_width,
        "height": chart_height,
        "backgroundColor": PAGE_BG,
        "marginLeft": 180,
        "marginRight": 50,
        "marginTop": 150,
        "marginBottom": 150,
    },
    "title": {
        "text": "horizon-basic · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
    },
    "subtitle": {
        "text": "<b style='color: %s'>Positive</b> (green) ↔ <b style='color: %s'>Negative</b> (orange) | Intensity = Magnitude"
        % (colors_pos[1], colors_neg[1]),
        "style": {"fontSize": "18px", "color": INK_SOFT},
        "y": 80,
    },
    "xAxis": {
        "min": 0,
        "max": 24,
        "tickInterval": 4,
        "title": {"text": "Hour of Day", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineWidth": 0,
    },
    "yAxis": y_axis_configs,
    "legend": {"enabled": False},
    "plotOptions": {"area": {"stacking": None, "animation": False}, "series": {"animation": False}},
    "series": series_configs,
    "credits": {"enabled": False},
}

# Convert to JS literal
chart_js = json.dumps(chart_options)

# Download Highcharts JS for inline embedding
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: {chart_width}px; height: {chart_height}px;"></div>
    <script>
        Highcharts.chart('container', {chart_js});
    </script>
</body>
</html>"""

# Save interactive HTML version with theme suffix
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")
chrome_options.add_argument("--hide-scrollbars")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(5000, 3000)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render

# Screenshot the chart container for exact dimensions
container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
