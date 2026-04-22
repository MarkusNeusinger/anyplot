""" pyplots.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Quarterly energy consumption by source with uncertainty
np.random.seed(42)
quarters = ["Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023", "Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]
n_points = len(quarters)

# Three energy sources with realistic seasonal patterns
# Solar: higher in summer, lower in winter
solar_base = np.array([15, 25, 30, 18, 17, 28, 32, 20])
solar_lower = solar_base - np.random.uniform(3, 6, n_points)
solar_upper = solar_base + np.random.uniform(3, 6, n_points)

# Wind: more variable, higher in winter
wind_base = np.array([28, 22, 18, 32, 30, 24, 20, 35])
wind_lower = wind_base - np.random.uniform(4, 8, n_points)
wind_upper = wind_base + np.random.uniform(4, 8, n_points)

# Hydro: relatively stable with seasonal variation
hydro_base = np.array([40, 45, 35, 38, 42, 48, 37, 40])
hydro_lower = hydro_base - np.random.uniform(5, 10, n_points)
hydro_upper = hydro_base + np.random.uniform(5, 10, n_points)

# Colors for each series
colors = {"Solar": "#FFD43B", "Wind": "#306998", "Hydro": "#17BECF"}

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "areaspline",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginTop": 120,
    "spacingBottom": 80,
}

# Title
chart.options.title = {
    "text": "area-stacked-confidence · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": "Renewable Energy Consumption by Source (GWh) with 90% Confidence Bands",
    "style": {"fontSize": "32px"},
}

# X-axis
chart.options.x_axis = {
    "categories": quarters,
    "title": {"text": "Quarter", "style": {"fontSize": "32px"}},
    "labels": {"style": {"fontSize": "24px"}},
    "crosshair": True,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Energy Consumption (GWh)", "style": {"fontSize": "32px"}},
    "labels": {"style": {"fontSize": "24px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "min": 0,
}

# Legend - positioned in top right corner to avoid bottom clipping
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "32px"},
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "top",
    "x": -50,
    "y": 100,
    "floating": True,
    "backgroundColor": "rgba(255, 255, 255, 0.9)",
    "borderWidth": 1,
    "borderColor": "#e0e0e0",
    "padding": 15,
}

# Tooltip
chart.options.tooltip = {
    "shared": True,
    "style": {"fontSize": "20px"},
    "headerFormat": "<b>{point.key}</b><br/>",
    "pointFormat": "{series.name}: {point.y:.1f} GWh<br/>",
}

# Plot options for stacking
chart.options.plot_options = {
    "areaspline": {
        "stacking": "normal",
        "lineWidth": 4,
        "marker": {"enabled": True, "radius": 8, "lineWidth": 2, "lineColor": "#ffffff"},
        "fillOpacity": 0.7,
    },
    "arearange": {
        "lineWidth": 0,
        "fillOpacity": 0.25,
        "marker": {"enabled": False},
        "enableMouseTracking": False,
        "linkedTo": ":previous",
    },
}

# Build series data - stacked areas with confidence bands
# For proper stacking with confidence bands, we need to calculate cumulative values
# The bands should show the range around each stacked layer

series_data = []

# Calculate cumulative bases for stacking
solar_cumulative = solar_base.copy()
wind_cumulative = solar_base + wind_base
hydro_cumulative = solar_base + wind_base + hydro_base

# Solar (bottom layer) - main series
series_data.append(
    {
        "name": "Solar",
        "type": "areaspline",
        "data": [float(v) for v in solar_base],
        "color": colors["Solar"],
        "fillColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [[0, colors["Solar"]], [1, colors["Solar"] + "40"]],
        },
    }
)

# Solar confidence band (arearange)
series_data.append(
    {
        "name": "Solar (90% CI)",
        "type": "arearange",
        "data": [[i, float(solar_lower[i]), float(solar_upper[i])] for i in range(n_points)],
        "color": colors["Solar"],
        "fillOpacity": 0.2,
        "showInLegend": False,
    }
)

# Wind (middle layer) - main series
series_data.append(
    {
        "name": "Wind",
        "type": "areaspline",
        "data": [float(v) for v in wind_base],
        "color": colors["Wind"],
        "fillColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [[0, colors["Wind"]], [1, colors["Wind"] + "40"]],
        },
    }
)

# Wind confidence band (stacked on top of solar)
wind_lower_stacked = solar_base + wind_lower
wind_upper_stacked = solar_base + wind_upper
series_data.append(
    {
        "name": "Wind (90% CI)",
        "type": "arearange",
        "data": [[i, float(wind_lower_stacked[i]), float(wind_upper_stacked[i])] for i in range(n_points)],
        "color": colors["Wind"],
        "fillOpacity": 0.2,
        "showInLegend": False,
    }
)

# Hydro (top layer) - main series
series_data.append(
    {
        "name": "Hydro",
        "type": "areaspline",
        "data": [float(v) for v in hydro_base],
        "color": colors["Hydro"],
        "fillColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [[0, colors["Hydro"]], [1, colors["Hydro"] + "40"]],
        },
    }
)

# Hydro confidence band (stacked on top of solar + wind)
hydro_lower_stacked = solar_base + wind_base + hydro_lower
hydro_upper_stacked = solar_base + wind_base + hydro_upper
series_data.append(
    {
        "name": "Hydro (90% CI)",
        "type": "arearange",
        "data": [[i, float(hydro_lower_stacked[i]), float(hydro_upper_stacked[i])] for i in range(n_points)],
        "color": colors["Hydro"],
        "fillOpacity": 0.2,
        "showInLegend": False,
    }
)

# Set series
chart.options.series = series_data

# Credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS and highcharts-more for arearange
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

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
