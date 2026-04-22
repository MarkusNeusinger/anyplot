""" pyplots.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Simulated daily product metrics over 6 months with event annotations
np.random.seed(42)

# Generate dates for 180 days
start_date = datetime(2024, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(180)]
timestamps = [int(d.timestamp() * 1000) for d in dates]  # Highcharts uses milliseconds

# Generate realistic user growth data with trend and seasonality
base = 10000
trend = np.linspace(0, 5000, 180)
seasonal = 500 * np.sin(np.linspace(0, 4 * np.pi, 180))
noise = np.random.randn(180) * 300
values = base + trend + seasonal + noise

# Define significant events to annotate
events = [
    (datetime(2024, 1, 15), "Feature A Launch"),
    (datetime(2024, 2, 20), "Marketing Campaign"),
    (datetime(2024, 3, 25), "App Redesign"),
    (datetime(2024, 4, 30), "Partnership Deal"),
    (datetime(2024, 5, 28), "Mobile Update"),
]
event_timestamps = [int(e[0].timestamp() * 1000) for e in events]
event_labels = [e[1] for e in events]

# Find y-values at event dates for scatter markers
event_y_values = []
for evt_date, _ in events:
    idx = (evt_date - start_date).days
    if 0 <= idx < len(values):
        event_y_values.append(round(values[idx]))
    else:
        event_y_values.append(None)

# Create chart with container specified
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration - explicit size for proper rendering
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "style": {"fontFamily": "Arial, sans-serif"},
}

# Title
chart.options.title = {
    "text": "line-annotated-events · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold", "color": "#333333"},
}

# Subtitle
chart.options.subtitle = {
    "text": "Daily Active Users with Key Milestones",
    "style": {"fontSize": "32px", "color": "#666666"},
}

# Build plot lines for events with alternating label positions
plot_lines = []
for i, (ts, label) in enumerate(zip(event_timestamps, event_labels, strict=False)):
    plot_lines.append(
        {
            "value": ts,
            "color": "#FFD43B",
            "width": 5,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": label,
                "rotation": 0,
                "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#333333"},
                "y": 25 if i % 2 == 0 else 70,
                "x": 12,
                "align": "left",
            },
        }
    )

# X-axis (datetime)
chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "40px", "color": "#333333"}},
    "labels": {"style": {"fontSize": "32px", "color": "#333333"}},
    "dateTimeLabelFormats": {"day": "%e %b", "week": "%e %b", "month": "%b '%y", "year": "%Y"},
    "plotLines": plot_lines,
    "lineColor": "#333333",
    "lineWidth": 2,
    "tickColor": "#333333",
    "tickInterval": 30 * 24 * 3600 * 1000,  # Monthly ticks
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Daily Active Users", "style": {"fontSize": "40px", "color": "#333333"}},
    "labels": {"style": {"fontSize": "32px", "color": "#333333"}},
    "gridLineWidth": 1,
    "gridLineColor": "#E0E0E0",
    "gridLineDashStyle": "Dash",
    "lineColor": "#333333",
    "lineWidth": 2,
}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "32px", "color": "#333333"},
    "align": "center",
    "verticalAlign": "bottom",
    "y": 30,
    "symbolRadius": 6,
    "symbolWidth": 24,
}

# Plot options for styling
chart.options.plot_options = {
    "line": {"lineWidth": 5, "marker": {"enabled": False}},
    "scatter": {"marker": {"symbol": "circle", "radius": 16, "lineWidth": 4, "lineColor": "#333333"}},
}

# Credits
chart.options.credits = {"enabled": False}

# Add main line series
line_series = LineSeries()
line_series.name = "Daily Active Users"
line_series.data = [[ts, round(val)] for ts, val in zip(timestamps, values, strict=False)]
line_series.color = "#306998"
line_series.line_width = 5
line_series.marker = {"enabled": False}

chart.add_series(line_series)

# Add event marker series (scatter points on the line at event dates)
event_series = ScatterSeries()
event_series.name = "Key Events"
event_series.data = [
    {"x": ts, "y": yval} for ts, yval in zip(event_timestamps, event_y_values, strict=False) if yval is not None
]
event_series.color = "#FFD43B"
event_series.marker = {"symbol": "circle", "radius": 18, "lineWidth": 4, "lineColor": "#333333", "fillColor": "#FFD43B"}
event_series.z_index = 10

chart.add_series(event_series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate chart JS code
chart_js = chart.to_js_literal()

# Build HTML with inline scripts - use string concatenation to avoid f-string issues
# with JavaScript template literals containing braces
html_parts = [
    "<!DOCTYPE html>",
    "<html>",
    "<head>",
    '    <meta charset="utf-8">',
    "    <style>",
    "        * { margin: 0; padding: 0; }",
    "        body { background: #ffffff; }",
    "        #container { width: 4800px; height: 2700px; }",
    "    </style>",
    "    <script>",
    highcharts_js,
    "    </script>",
    "</head>",
    "<body>",
    '    <div id="container"></div>',
    "    <script>",
    chart_js,
    "    </script>",
    "</body>",
    "</html>",
]
html_content = "\n".join(html_parts)

# Write temp HTML
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML file for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(5000, 3000)
driver.get(f"file://{temp_path}")
time.sleep(6)  # Wait for chart to render

# Find the chart container and take screenshot of it
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
