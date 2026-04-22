""" pyplots.ai
area-stacked: Stacked Area Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Monthly revenue by product category (in thousands $) over 2 years
months = [
    "Jan 2023",
    "Feb 2023",
    "Mar 2023",
    "Apr 2023",
    "May 2023",
    "Jun 2023",
    "Jul 2023",
    "Aug 2023",
    "Sep 2023",
    "Oct 2023",
    "Nov 2023",
    "Dec 2023",
    "Jan 2024",
    "Feb 2024",
    "Mar 2024",
    "Apr 2024",
    "May 2024",
    "Jun 2024",
    "Jul 2024",
    "Aug 2024",
    "Sep 2024",
    "Oct 2024",
    "Nov 2024",
    "Dec 2024",
]

# Revenue data by category (stacked from bottom to top: largest first)
electronics = [
    120,
    135,
    145,
    160,
    175,
    190,
    210,
    225,
    195,
    180,
    240,
    280,
    130,
    145,
    155,
    175,
    195,
    210,
    235,
    250,
    215,
    195,
    265,
    310,
]
software = [
    80,
    85,
    95,
    105,
    115,
    120,
    125,
    130,
    135,
    140,
    150,
    165,
    90,
    95,
    105,
    115,
    130,
    140,
    150,
    160,
    165,
    170,
    185,
    200,
]
services = [45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 110, 50, 55, 60, 70, 75, 85, 90, 100, 105, 115, 125, 140]
accessories = [25, 28, 32, 35, 40, 45, 48, 52, 48, 45, 55, 70, 28, 32, 36, 42, 48, 52, 58, 62, 55, 52, 65, 85]

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "spacingBottom": 100,
    "style": {"fontFamily": "Arial, sans-serif"},
}

# Title
chart.options.title = {
    "text": "area-stacked · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
}

chart.options.subtitle = {"text": "Monthly Revenue by Product Category (2023-2024)", "style": {"fontSize": "36px"}}

# X-axis
chart.options.x_axis = {
    "categories": months,
    "title": {"text": "Month", "style": {"fontSize": "36px"}, "y": 50},
    "labels": {"style": {"fontSize": "26px"}, "y": 35},
    "tickmarkPlacement": "on",
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Revenue ($ thousands)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineColor": "#e0e0e0",
    "gridLineWidth": 1,
}

# Legend - positioned at top right for better visibility
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "itemStyle": {"fontSize": "32px"},
    "x": -50,
    "y": 100,
    "backgroundColor": "#ffffff",
    "borderWidth": 1,
    "borderColor": "#cccccc",
    "padding": 15,
}

# Plot options for stacked area
chart.options.plot_options = {
    "area": {
        "stacking": "normal",
        "lineWidth": 2,
        "marker": {"enabled": False, "radius": 6, "states": {"hover": {"enabled": True}}},
        "fillOpacity": 0.75,
    }
}

# Tooltip
chart.options.tooltip = {
    "shared": True,
    "style": {"fontSize": "24px"},
    "headerFormat": '<span style="font-size: 28px">{point.key}</span><br/>',
    "pointFormat": '<span style="color:{series.color}">\u25cf</span> {series.name}: <b>${point.y}K</b><br/>',
}

# Colorblind-safe palette (Python Blue, Yellow, Purple, Cyan)
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF"]

# Add series (ordered from bottom to top by average size)
series_data = [
    ("Electronics", electronics, colors[0]),
    ("Software", software, colors[1]),
    ("Services", services, colors[2]),
    ("Accessories", accessories, colors[3]),
]

for name, data, color in series_data:
    series = AreaSeries()
    series.name = name
    series.data = data
    series.color = color
    chart.add_series(series)

# Download Highcharts JS for headless Chrome
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
<body style="margin:0; padding:0;">
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
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

# Save HTML for interactive version
Path("plot.html").write_text(html_content, encoding="utf-8")

# Clean up temp file
Path(temp_path).unlink()
