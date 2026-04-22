""" pyplots.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import BarSeries, ColumnSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - bivariate normal with correlation (realistic sensor data scenario)
np.random.seed(42)
n_points = 150
# Temperature sensor readings (Celsius)
temperature = np.random.randn(n_points) * 5 + 25
# Humidity readings (%) - correlated with temperature
humidity = -1.2 * temperature + 80 + np.random.randn(n_points) * 8

# Axis ranges for alignment
x_min, x_max = float(temperature.min()), float(temperature.max())
y_min, y_max = float(humidity.min()), float(humidity.max())
x_range = x_max - x_min
y_range = y_max - y_min
x_padding = x_range * 0.05
y_padding = y_range * 0.05

# Calculate histogram bins for marginal distributions
n_bins = 15
x_hist, x_edges = np.histogram(temperature, bins=n_bins, range=(x_min - x_padding, x_max + x_padding))
y_hist, y_edges = np.histogram(humidity, bins=n_bins, range=(y_min - y_padding, y_max + y_padding))

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Shared axis bounds for alignment
scatter_x_min = x_min - x_padding
scatter_x_max = x_max + x_padding
scatter_y_min = y_min - y_padding
scatter_y_max = y_max + y_padding

# Chart dimensions - no gaps between charts
main_width = 3400
main_height = 2200
top_height = 400
right_width = 500
margin_left = 140
margin_bottom = 140
margin_top = 60
margin_right = 60

# Create the main scatter chart
main_chart = Chart(container="main-chart")
main_chart.options = HighchartsOptions()

main_chart.options.chart = {
    "type": "scatter",
    "width": main_width,
    "height": main_height,
    "backgroundColor": "#ffffff",
    "marginTop": margin_top,
    "marginRight": margin_right,
    "marginBottom": margin_bottom,
    "marginLeft": margin_left,
    "spacing": [0, 0, 0, 0],
}

main_chart.options.title = {"text": ""}
main_chart.options.subtitle = {"text": ""}
main_chart.options.caption = {"text": ""}

main_chart.options.x_axis = {
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "32px", "color": "#333333"}},
    "labels": {"style": {"fontSize": "26px", "color": "#333333"}},
    "min": scatter_x_min,
    "max": scatter_x_max,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
    "lineWidth": 2,
    "lineColor": "#333333",
    "tickInterval": 5,
}

main_chart.options.y_axis = {
    "title": {"text": "Relative Humidity (%)", "style": {"fontSize": "32px", "color": "#333333"}},
    "labels": {"style": {"fontSize": "26px", "color": "#333333"}},
    "min": scatter_y_min,
    "max": scatter_y_max,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
    "lineWidth": 2,
    "lineColor": "#333333",
}

main_chart.options.legend = {"enabled": False}
main_chart.options.credits = {"enabled": False}
main_chart.options.exporting = {"enabled": False}

main_chart.options.plot_options = {
    "scatter": {
        "marker": {"radius": 12, "fillColor": "rgba(48, 105, 152, 0.45)", "lineWidth": 1, "lineColor": "#306998"}
    }
}

# Add scatter series
scatter_series = ScatterSeries()
scatter_series.data = [[float(xi), float(yi)] for xi, yi in zip(temperature, humidity, strict=True)]
scatter_series.name = "Sensor Readings"
scatter_series.color = "#306998"
main_chart.add_series(scatter_series)

# Create top histogram (X marginal) - using column chart with continuous x-axis
top_chart = Chart(container="top-chart")
top_chart.options = HighchartsOptions()

top_chart.options.chart = {
    "type": "column",
    "width": main_width,
    "height": top_height,
    "backgroundColor": "#ffffff",
    "marginTop": 100,
    "marginRight": margin_right,
    "marginBottom": 0,
    "marginLeft": margin_left,
    "spacing": [0, 0, 0, 0],
}

top_chart.options.title = {
    "text": "scatter-marginal · highcharts · pyplots.ai",
    "style": {"fontSize": "42px", "fontWeight": "bold", "color": "#333333"},
    "align": "center",
}
top_chart.options.subtitle = {"text": ""}
top_chart.options.caption = {"text": ""}

# Use continuous x-axis matching scatter plot range
top_chart.options.x_axis = {
    "labels": {"enabled": False},
    "title": {"text": "", "enabled": False},
    "lineWidth": 0,
    "tickWidth": 0,
    "min": scatter_x_min,
    "max": scatter_x_max,
    "gridLineWidth": 0,
}

top_chart.options.y_axis = {
    "title": {"text": "", "enabled": False},
    "labels": {"style": {"fontSize": "22px", "color": "#333333"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
    "min": 0,
}

top_chart.options.legend = {"enabled": False}
top_chart.options.credits = {"enabled": False}
top_chart.options.exporting = {"enabled": False}

# Calculate bar width based on bin width
bin_width = (scatter_x_max - scatter_x_min) / n_bins

top_chart.options.plot_options = {
    "column": {
        "borderWidth": 1,
        "borderColor": "#306998",
        "pointPadding": 0,
        "groupPadding": 0,
        "pointWidth": None,
        "pointRange": bin_width * 0.9,
    }
}

# Add histogram series for top - using x,y pairs for proper alignment
top_series = ColumnSeries()
top_series.data = [{"x": float((x_edges[i] + x_edges[i + 1]) / 2), "y": int(x_hist[i])} for i in range(len(x_hist))]
top_series.name = "Temperature Distribution"
top_series.color = "rgba(48, 105, 152, 0.5)"
top_chart.add_series(top_series)

# Create right histogram (Y marginal) - using bar chart for horizontal bars
right_chart = Chart(container="right-chart")
right_chart.options = HighchartsOptions()

right_chart.options.chart = {
    "type": "bar",
    "width": right_width,
    "height": main_height,
    "backgroundColor": "#ffffff",
    "marginTop": margin_top,
    "marginRight": 120,
    "marginBottom": margin_bottom,
    "marginLeft": 0,
    "spacing": [0, 0, 0, 0],
}

right_chart.options.title = {"text": ""}
right_chart.options.subtitle = {"text": ""}
right_chart.options.caption = {"text": ""}

# Use continuous x-axis (which becomes y after bar rotation) matching scatter y range
right_chart.options.x_axis = {
    "labels": {"enabled": False},
    "title": {"text": "", "enabled": False},
    "lineWidth": 0,
    "tickWidth": 0,
    "min": scatter_y_min,
    "max": scatter_y_max,
    "gridLineWidth": 0,
    "reversed": False,
}

right_chart.options.y_axis = {
    "title": {"text": "", "enabled": False},
    "labels": {"style": {"fontSize": "22px", "color": "#333333"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
    "opposite": True,
    "reversed": False,
    "min": 0,
}

right_chart.options.legend = {"enabled": False}
right_chart.options.credits = {"enabled": False}
right_chart.options.exporting = {"enabled": False}

# Calculate bar height based on bin width
y_bin_width = (scatter_y_max - scatter_y_min) / n_bins

right_chart.options.plot_options = {
    "bar": {
        "borderWidth": 1,
        "borderColor": "#306998",
        "pointPadding": 0,
        "groupPadding": 0,
        "pointRange": y_bin_width * 0.9,
    }
}

# Add histogram series for right - using x,y pairs for proper alignment
right_series = BarSeries()
right_series.data = [{"x": float((y_edges[i] + y_edges[i + 1]) / 2), "y": int(y_hist[i])} for i in range(len(y_hist))]
right_series.name = "Humidity Distribution"
right_series.color = "rgba(48, 105, 152, 0.5)"
right_chart.add_series(right_series)

# Generate JS literals
main_js = main_chart.to_js_literal()
top_js = top_chart.to_js_literal()
right_js = right_chart.to_js_literal()

# Total dimensions
total_width = main_width + right_width
total_height = top_height + main_height

# Create combined HTML with all three charts - seamless layout with no gaps
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: #ffffff;
            width: {total_width}px;
            height: {total_height}px;
            overflow: hidden;
        }}
        #top-chart {{
            position: absolute;
            top: 0;
            left: 0;
            width: {main_width}px;
            height: {top_height}px;
        }}
        #corner {{
            position: absolute;
            top: 0;
            left: {main_width}px;
            width: {right_width}px;
            height: {top_height}px;
            background: #ffffff;
        }}
        #main-chart {{
            position: absolute;
            top: {top_height}px;
            left: 0;
            width: {main_width}px;
            height: {main_height}px;
        }}
        #right-chart {{
            position: absolute;
            top: {top_height}px;
            left: {main_width}px;
            width: {right_width}px;
            height: {main_height}px;
        }}
    </style>
</head>
<body>
    <div id="top-chart"></div>
    <div id="corner"></div>
    <div id="main-chart"></div>
    <div id="right-chart"></div>
    <script>
        // Override Highcharts defaults to remove "Chart title"
        Highcharts.setOptions({{
            lang: {{
                chartTitle: ''
            }},
            title: {{
                text: ''
            }}
        }});
        {top_js}
        {main_js}
        {right_js}
    </script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument(f"--window-size={total_width + 100},{total_height + 100}")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for charts to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
