""" anyplot.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: highcharts unknown | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-09
"""

import http.server
import os
import shutil
import socketserver
import tempfile
import threading
import time
import urllib.request

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import BarSeries, ColumnSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - bivariate normal with correlation (realistic sensor data scenario)
np.random.seed(42)
n_points = 150
temperature = np.random.randn(n_points) * 5 + 25
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
# Try multiple CDN sources
cdns = ["https://cdn.jsdelivr.net/npm/highcharts@11.4.0/highcharts.min.js", "https://code.highcharts.com/highcharts.js"]
highcharts_js = ""
for cdn_url in cdns:
    try:
        if REQUESTS_AVAILABLE:
            response = requests.get(cdn_url, timeout=30)
            response.raise_for_status()
            highcharts_js = response.text
            break
        else:
            req = urllib.request.Request(cdn_url)
            req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
                break
    except Exception:
        continue
if not highcharts_js:
    print("Warning: Failed to download Highcharts JS from all CDNs. Using external CDN link in HTML.")

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
    "backgroundColor": PAGE_BG,
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
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "32px", "color": INK}},
    "labels": {"style": {"fontSize": "26px", "color": INK_SOFT}},
    "min": scatter_x_min,
    "max": scatter_x_max,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dash",
    "lineWidth": 2,
    "lineColor": INK_SOFT,
    "tickInterval": 5,
    "tickColor": INK_SOFT,
}

main_chart.options.y_axis = {
    "title": {"text": "Relative Humidity (%)", "style": {"fontSize": "32px", "color": INK}},
    "labels": {"style": {"fontSize": "26px", "color": INK_SOFT}},
    "min": scatter_y_min,
    "max": scatter_y_max,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dash",
    "lineWidth": 2,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

main_chart.options.legend = {"enabled": False}
main_chart.options.credits = {"enabled": False}
main_chart.options.exporting = {"enabled": False}

main_chart.options.plot_options = {
    "scatter": {"marker": {"radius": 12, "fillColor": BRAND, "lineWidth": 1, "lineColor": PAGE_BG, "opacity": 0.7}}
}

# Add scatter series
scatter_series = ScatterSeries()
scatter_series.data = [[float(xi), float(yi)] for xi, yi in zip(temperature, humidity, strict=True)]
scatter_series.name = "Sensor Readings"
scatter_series.color = BRAND
main_chart.add_series(scatter_series)

# Create top histogram (X marginal) - using column chart with continuous x-axis
top_chart = Chart(container="top-chart")
top_chart.options = HighchartsOptions()

top_chart.options.chart = {
    "type": "column",
    "width": main_width,
    "height": top_height,
    "backgroundColor": PAGE_BG,
    "marginTop": 100,
    "marginRight": margin_right,
    "marginBottom": 0,
    "marginLeft": margin_left,
    "spacing": [0, 0, 0, 0],
}

top_chart.options.title = {
    "text": "scatter-marginal · highcharts · anyplot.ai",
    "style": {"fontSize": "42px", "fontWeight": "bold", "color": INK},
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
    "labels": {"style": {"fontSize": "22px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
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
        "borderColor": BRAND,
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
top_series.color = BRAND
top_chart.add_series(top_series)

# Create right histogram (Y marginal) - using bar chart for horizontal bars
right_chart = Chart(container="right-chart")
right_chart.options = HighchartsOptions()

right_chart.options.chart = {
    "type": "bar",
    "width": right_width,
    "height": main_height,
    "backgroundColor": PAGE_BG,
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
    "labels": {"style": {"fontSize": "22px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
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
        "borderColor": BRAND,
        "pointPadding": 0,
        "groupPadding": 0,
        "pointRange": y_bin_width * 0.9,
    }
}

# Add histogram series for right - using x,y pairs for proper alignment
right_series = BarSeries()
right_series.data = [{"x": float((y_edges[i] + y_edges[i + 1]) / 2), "y": int(y_hist[i])} for i in range(len(y_hist))]
right_series.name = "Humidity Distribution"
right_series.color = BRAND
right_chart.add_series(right_series)

# Generate JS literals
main_js = main_chart.to_js_literal()
top_js = top_chart.to_js_literal()
right_js = right_chart.to_js_literal()

# Total dimensions
total_width = main_width + right_width
total_height = top_height + main_height

# Create combined HTML with all three charts - seamless layout with no gaps
if highcharts_js:
    script_tag = f"<script>{highcharts_js}</script>"
else:
    script_tag = '<script src="https://code.highcharts.com/highcharts.js"></script>'

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    {script_tag}
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: {PAGE_BG};
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
            background: {PAGE_BG};
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

# Get current working directory before any changes
cwd = os.getcwd()

# Save HTML for interactive viewing
with open(os.path.join(cwd, f"plot-{THEME}.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML
temp_dir = tempfile.mkdtemp()
temp_path = os.path.join(temp_dir, "chart.html")
with open(temp_path, "w", encoding="utf-8") as f:
    f.write(html_content)


# Start simple HTTP server in background thread
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


os.chdir(temp_dir)

# Find an available port
with socketserver.TCPServer(("127.0.0.1", 0), QuietHandler) as httpd:
    PORT = httpd.server_address[1]  # Get the actual port assigned
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    time.sleep(1)  # Give server time to start

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--window-size={total_width + 100},{total_height + 100}")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(f"http://127.0.0.1:{PORT}/chart.html")
    time.sleep(10)  # Wait for Highcharts to load and render
    driver.save_screenshot(os.path.join(cwd, f"plot-{THEME}.png"))
    driver.quit()

    httpd.shutdown()

# Clean up
shutil.rmtree(temp_dir, ignore_errors=True)
